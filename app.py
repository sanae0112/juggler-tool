import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

st.set_page_config(page_title="Juggler Analyzer PRO", layout="wide")
st.title("🎰 Juggler Analyzer PRO")

# ======================
# Google Sheets 接続
# ======================
def connect_sheet():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    client = gspread.authorize(creds)
    sheet = client.open("juggler_data").sheet1

    return sheet

# ======================
# LINE通知
# ======================
def send_line(msg):

    token = st.secrets["LINE_TOKEN"]

    url = "https://notify-api.line.me/api/notify"

    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": msg}

    requests.post(url, headers=headers, data=data)

# ======================
# 基本入力
# ======================
machine = st.selectbox("機種",[
"アイムジャグラーEX",
"マイジャグラーV"
])

seat = st.number_input("台番号",0)

# ======================
# 回転
# ======================
st.header("🎮回転")

if "spin" not in st.session_state:
    st.session_state.spin = 0

c1,c2 = st.columns(2)

with c1:
    if st.button("+1"):
        st.session_state.spin += 1

with c2:
    if st.button("+10"):
        st.session_state.spin += 10

spin = st.number_input("現在回転",0,value=st.session_state.spin)
prev_spin = st.number_input("前任者回転",0)

total_spin = spin + prev_spin

# ======================
# カウンター関数
# ======================
def counter(label,key):
    if key not in st.session_state:
        st.session_state[key]=0

    c1,c2=st.columns([1,2])

    with c1:
        if st.button(label,key=key):
            st.session_state[key]+=1

    with c2:
        st.write(st.session_state[key])

    return st.session_state[key]

# ======================
# 小役
# ======================
st.header("🍒小役")

grape = counter("🍇ぶどう+1","g")
cherry = counter("🍒チェリー+1","c")
middle_cherry = counter("🍒中段+1","mc")

# ======================
# ボーナス
# ======================
st.header("🎰ボーナス")

big_total = counter("🔴ビック+1","b")
reg_total = counter("🔵バケ+1","r")

# ======================
# 確率
# ======================
st.header("📊確率")

if total_spin > 0:

    total = big_total + reg_total

    if total > 0:
        st.write("合算 1/", round(total_spin/total,1))

    if big_total > 0:
        st.write("ビック 1/", round(total_spin/big_total,1))

    if reg_total > 0:
        st.write("バケ 1/", round(total_spin/reg_total,1))

    if grape > 0:
        st.write("ぶどう 1/", round(total_spin/grape,2))

# ======================
# 設定期待度
# ======================
st.header("🎰設定期待度")

if total_spin > 0 and reg_total > 0:

    reg_rate = total_spin / reg_total

    if reg_rate > 350:
        level = 20
    elif reg_rate > 300:
        level = 40
    elif reg_rate > 260:
        level = 60
    elif reg_rate > 230:
        level = 80
    else:
        level = 100

    st.progress(level)

# ======================
# グラフ
# ======================
st.header("📈設定6比較")

if total_spin > 0:

    spins = list(range(500,total_spin+1,500))
    fig = go.Figure()

    if reg_total > 0:
        actual = [total_spin/reg_total for _ in spins]
        fig.add_trace(go.Scatter(x=spins,y=actual,name="実測"))

    fig.add_trace(go.Scatter(
        x=spins,
        y=[255 for _ in spins],
        name="設定6",
        line=dict(dash="dash")
    ))

    st.plotly_chart(fig)

# ======================
# 保存
# ======================
st.header("💾保存")

investment = st.number_input("投資",0)
recovery = st.number_input("回収",0)

if st.button("保存"):

    sheet = connect_sheet()
    now = datetime.datetime.now()

    sheet.append_row([
        now.strftime("%Y-%m-%d %H:%M"),
        machine,
        seat,
        total_spin,
        prev_spin,
        grape,
        cherry,
        middle_cherry,
        big_total,
        reg_total,
        investment,
        recovery
    ])

    st.success("保存完了")

# ======================
# 判定AI
# ======================
def judge(row):

    try:
        spin = float(row["現在回転"])
        reg = float(row["バケ"])
        grape = float(row["ぶどう"])
    except:
        return 0

    if spin==0 or reg==0 or grape==0:
        return 0

    score = 0

    if spin/reg < 260:
        score += 50
    elif spin/reg < 300:
        score += 30

    if spin/grape < 6.1:
        score += 30
    elif spin/grape < 6.3:
        score += 15

    if spin > 3000:
        score += 20
    elif spin > 1500:
        score += 10

    return score

# ======================
# 狙い台AI
# ======================
st.header("🤖狙い台")

if st.button("狙い台検索"):

    sheet = connect_sheet()
    data = sheet.get_all_values()

    df = pd.DataFrame(data[1:], columns=data[0])

    df["スコア"] = df.apply(judge, axis=1)
    df = df.sort_values("スコア", ascending=False)

    st.dataframe(df.head(10))

# ======================
# 通知
# ======================
st.header("📲通知")

if st.button("狙い台通知"):

    sheet = connect_sheet()
    data = sheet.get_all_values()

    df = pd.DataFrame(data[1:], columns=data[0])

    df["スコア"] = df.apply(judge, axis=1)

    hot = df[df["スコア"] > 70]

    for _, row in hot.iterrows():

        msg = f"""
🔥狙い台🔥
台{row["台番号"]}
回転{row["現在回転"]}
スコア{round(row["スコア"],1)}
"""

        send_line(msg)

    st.success("通知完了")

# ======================
# 曜日分析
# ======================
st.header("📅曜日分析")

if st.button("曜日分析"):

    sheet = connect_sheet()
    data = sheet.get_all_values()

    df = pd.DataFrame(data[1:], columns=data[0])

    df["日時"] = pd.to_datetime(df["日時"], errors="coerce")
    df["曜日"] = df["日時"].dt.day_name()

    df["回転"] = pd.to_numeric(df["現在回転"], errors="coerce")
    df["バケ"] = pd.to_numeric(df["バケ"], errors="coerce")

    df["バケ確率"] = df["回転"] / df["バケ"]

    summary = df.groupby("曜日")["バケ確率"].mean()

    st.dataframe(summary)

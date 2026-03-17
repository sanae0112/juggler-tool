import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Juggler Analyzer PRO", layout="wide")
st.title("🎰 Juggler Analyzer PRO")

# ======================
# Google Sheets接続
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
# ホール入力（履歴＋手入力）
# ======================
def get_shop_list():
    try:
        sheet = connect_sheet()
        data = sheet.get_all_values()

        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            shops = df["ホール"].dropna().unique().tolist()
            return [""] + sorted(shops)
        else:
            return [""]
    except:
        return [""]

shop_list = get_shop_list()

col1, col2 = st.columns(2)

with col1:
    selected_shop = st.selectbox("ホール選択", shop_list)

with col2:
    new_shop = st.text_input("新規ホール")

shop = new_shop if new_shop != "" else selected_shop

# ======================
# 基本
# ======================
machine = st.selectbox("機種",[
"アイムジャグラーEX","マイジャグラーV"
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
middle_cherry = counter("🍒中段チェリー+1","mc")

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

    if cherry > 0:
        st.write("チェリー 1/", round(total_spin/cherry,2))

# ======================
# 設定期待度
# ======================
st.header("🎯設定期待度")

if total_spin > 0 and reg_total > 0:
    reg_rate = total_spin / reg_total

    if reg_rate < 230:
        level = 100
    elif reg_rate < 260:
        level = 80
    elif reg_rate < 300:
        level = 60
    else:
        level = 30

    st.progress(level)

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
        shop,
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
# 💰収支フル分析
# ======================
st.header("💰収支分析")

if st.button("収支を見る"):

    sheet = connect_sheet()
    data = sheet.get_all_values()

    df = pd.DataFrame(data[1:], columns=data[0])

    if len(df) > 0:

        df["投資"] = pd.to_numeric(df["投資"], errors="coerce")
        df["回収"] = pd.to_numeric(df["回収"], errors="coerce")
        df["収支"] = df["回収"] - df["投資"]

        df["日時"] = pd.to_datetime(df["日時"], errors="coerce")
        df["日付"] = df["日時"].dt.date
        df["月"] = df["日時"].dt.to_period("M")
        df["年"] = df["日時"].dt.year

        st.subheader("💰総収支")
        st.write(int(df["収支"].sum()), "円")

        st.subheader("📅日別")
        daily = df.groupby("日付")["収支"].sum()
        st.line_chart(daily)

        st.subheader("📆月別")
        monthly = df.groupby("月")["収支"].sum()
        st.bar_chart(monthly)

        st.subheader("📊年別")
        yearly = df.groupby("年")["収支"].sum()
        st.bar_chart(yearly)

        st.subheader("🏠ホール別")
        shop_profit = df.groupby("ホール")["収支"].sum().sort_values(ascending=False)
        st.bar_chart(shop_profit)

        st.subheader("🎯勝率")
        win_rate = (df["収支"] > 0).mean() * 100
        st.write(round(win_rate,1), "%")

        st.subheader("📈累計")
        st.line_chart(daily.cumsum())

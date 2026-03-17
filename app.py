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
    return client.open("juggler_data").sheet1

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
# ホール入力
# ======================
def get_shop_list():
    try:
        sheet = connect_sheet()
        data = sheet.get_all_values()
        if len(data)>1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return [""] + sorted(df["ホール"].dropna().unique())
    except:
        pass
    return [""]

shops = get_shop_list()

c1,c2 = st.columns(2)

with c1:
    selected = st.selectbox("ホール選択", shops)

with c2:
    new = st.text_input("新規ホール")

shop = new if new else selected

# ======================
# 基本
# ======================
machine = st.selectbox("機種",["アイム","マイ"])
seat = st.number_input("台番号",0)

# ======================
# 回転
# ======================
st.header("🎮回転")

if "spin" not in st.session_state:
    st.session_state.spin = 0

if st.button("+1"):
    st.session_state.spin += 1
if st.button("+10"):
    st.session_state.spin += 10

spin = st.number_input("現在回転",0,value=st.session_state.spin)
prev_spin = st.number_input("前任者回転",0)

total_spin = spin + prev_spin

# ======================
# 小役
# ======================
st.header("🍒小役")

grape = counter("🍇ぶどう","g")
cherry = counter("🍒チェリー","c")
middle = counter("🍒中段チェリー","mc")

# ======================
# ビック内訳
# ======================
st.header("🔴ビック内訳")

b1 = counter("単独ビック","b1")
b2 = counter("チェリービック","b2")
b3 = counter("ピエロビック","b3")
b4 = counter("一枚役ビック","b4")

big_total = b1 + b2 + b3 + b4

# ======================
# バケ内訳
# ======================
st.header("🔵バケ内訳")

r1 = counter("単独バケ","r1")
r2 = counter("チェリーバケ","r2")
r3 = counter("ピエロバケ","r3")
r4 = counter("一枚役バケ","r4")

reg_total = r1 + r2 + r3 + r4

# ======================
# 確率
# ======================
st.header("📊確率")

if total_spin>0:

    total = big_total + reg_total

    if total>0:
        st.write("合算 1/", round(total_spin/total,1))

    if big_total>0:
        st.write("ビック 1/", round(total_spin/big_total,1))

    if reg_total>0:
        st.write("バケ 1/", round(total_spin/reg_total,1))

    if grape>0:
        st.write("ぶどう 1/", round(total_spin/grape,2))

    if cherry>0:
        st.write("チェリー 1/", round(total_spin/cherry,2))

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
        middle,
        b1,b2,b3,b4,
        r1,r2,r3,r4,
        investment,
        recovery
    ])

    st.success("保存完了")

# ======================
# 収支分析
# ======================
st.header("💰収支分析")

if st.button("収支を見る"):

    sheet = connect_sheet()
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])

    if len(df)>0:

        df["投資"] = pd.to_numeric(df["投資"], errors="coerce")
        df["回収"] = pd.to_numeric(df["回収"], errors="coerce")
        df["収支"] = df["回収"] - df["投資"]

        df["日時"] = pd.to_datetime(df["日時"], errors="coerce")
        df["日付"] = df["日時"].dt.date
        df["月"] = df["日時"].dt.to_period("M")
        df["年"] = df["日時"].dt.year

        st.write("総収支", int(df["収支"].sum()))

        st.line_chart(df.groupby("日付")["収支"].sum().cumsum())

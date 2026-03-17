import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Juggler Analyzer", layout="wide")

st.title("🎰 Juggler Analyzer")

# ======================
# Google Sheets 接続
# ======================

def connect_sheet():

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    sheet = client.open("juggler_data").sheet1

    return sheet

# ======================
# 機種選択
# ======================

machine = st.selectbox(
"機種",
[
"アイムジャグラーEX",
"マイジャグラーV",
"ファンキージャグラー2",
"ゴーゴージャグラー3",
"ハッピージャグラーV3",
"ミスタージャグラー",
"ウルトラミラクルジャグラー",
"ジャグラーガールズSS"
]
)

# ======================
# 実戦カウンター
# ======================

st.header("📱実戦カウンター")

if "spin_count" not in st.session_state:
    st.session_state.spin_count = 0

colA,colB = st.columns(2)

with colA:
    if st.button("回転 +1"):
        st.session_state.spin_count += 1

with colB:
    if st.button("回転 +10"):
        st.session_state.spin_count += 10

spin = st.number_input("回転数",0,value=st.session_state.spin_count)

# ======================
# 小役
# ======================

st.header("🍒小役")

c1,c2,c3 = st.columns(3)

with c1:
    grape = st.number_input("🍇ぶどう",0)

with c2:
    cherry = st.number_input("🍒チェリー",0)

with c3:
    cherry_no = st.number_input("非重複チェリー",0)

middle_cherry = st.number_input("中段チェリー",0)

# ======================
# BIG
# ======================

st.header("🔴BIG内訳")

b1,b2,b3 = st.columns(3)

with b1:
    big_single = st.number_input("単独BIG",0)

with b2:
    big_cherry = st.number_input("チェリーBIG",0)

with b3:
    big_rare = st.number_input("レアチェリーBIG",0)

b4,b5 = st.columns(2)

with b4:
    big_pierrot = st.number_input("ピエロBIG",0)

with b5:
    big_one = st.number_input("一枚役BIG",0)

# ======================
# REG
# ======================

st.header("🔵REG内訳")

r1,r2,r3 = st.columns(3)

with r1:
    reg_single = st.number_input("単独REG",0)

with r2:
    reg_cherry = st.number_input("チェリーREG",0)

with r3:
    reg_rare = st.number_input("レアチェリーREG",0)

r4,r5 = st.columns(2)

with r4:
    reg_pierrot = st.number_input("ピエロREG",0)

with r5:
    reg_one = st.number_input("一枚役REG",0)

# ======================
# 合計
# ======================

big_total = big_single + big_cherry + big_rare + big_pierrot + big_one
reg_total = reg_single + reg_cherry + reg_rare + reg_pierrot + reg_one

# ======================
# 確率計算
# ======================

st.header("📊確率")

if spin > 0:

    total = big_total + reg_total

    if total > 0:
        st.write("合算 1/", round(spin/total,1))

    if big_total > 0:
        st.write("BIG 1/", round(spin/big_total,1))

    if reg_total > 0:
        st.write("REG 1/", round(spin/reg_total,1))

    if grape > 0:
        st.write("ぶどう 1/", round(spin/grape,1))

    if cherry > 0:
        st.write("チェリー 1/", round(spin/cherry,1))

# ======================
# 確率推移
# ======================

st.header("📈確率推移")

if spin > 0:

    spins = list(range(500,spin+1,500))

    grape_rate = [spin/grape if grape>0 else 0 for _ in spins]
    reg_rate = [spin/reg_total if reg_total>0 else 0 for _ in spins]

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=spins,y=grape_rate,mode="lines",name="ぶどう"))
    fig.add_trace(go.Scatter(x=spins,y=reg_rate,mode="lines",name="REG"))

    st.plotly_chart(fig)

# ======================
# AI設定推測
# ======================

st.header("🤖設定推測AI")

REG_SETTING={
1:439,
2:399,
3:331,
4:315,
5:255,
6:255
}

def estimate(spin,reg):

    if reg==0:
        return None

    probs={}

    for s,p in REG_SETTING.items():

        lam=spin/p
        prob=np.exp(-lam)*lam**reg
        probs[s]=prob

    total=sum(probs.values())

    for s in probs:
        probs[s]=probs[s]/total*100

    return probs

if spin>0:

    result=estimate(spin,reg_total)

    if result:

        df=pd.DataFrame(list(result.items()),columns=["設定","確率%"])

        st.bar_chart(df.set_index("設定"))

        high=result.get(4,0)+result.get(5,0)+result.get(6,0)

        st.write("設定4以上期待度",round(high,1),"%")

# ======================
# 保存
# ======================

st.header("💾データ保存")

investment=st.number_input("投資",0)
recovery=st.number_input("回収",0)

if st.button("保存"):

    sheet=connect_sheet()

    now=datetime.datetime.now()

    sheet.append_row([
        now.strftime("%Y-%m-%d %H:%M"),
        machine,
        spin,
        grape,
        cherry,
        cherry_no,
        middle_cherry,
        big_single,
        big_cherry,
        big_rare,
        big_pierrot,
        big_one,
        reg_single,
        reg_cherry,
        reg_rare,
        reg_pierrot,
        reg_one,
        investment,
        recovery
    ])

    st.success("保存しました")

# ======================
# 履歴
# ======================

st.header("📊履歴分析")

if st.button("履歴読み込み"):

    sheet=connect_sheet()

    data=sheet.get_all_records()

    df=pd.DataFrame(data)

    st.dataframe(df)

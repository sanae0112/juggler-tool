import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import binom
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

st.set_page_config(page_title="Juggler Analyzer PRO", layout="wide")

st.title("🎰 Juggler Analyzer PRO")

# ==============================
# Google Sheets 接続
# ==============================

def connect_sheet():

    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope
        )

        client = gspread.authorize(creds)
        sheet = client.open("juggler_data").sheet1

        return sheet

    except:
        return None


# ==============================
# ジャグラースペック
# ==============================

specs = {

"アイムジャグラーEX":{
"big":[273,270,266,254,240,229],
"reg":[439,399,331,290,268,229],
"grape":[6.14,6.10,6.05,6.02,5.98,5.95],
"payout":[97,98,101,104,107,109]
},

"マイジャグラーV":{
"big":[273,270,266,254,240,229],
"reg":[409,399,331,290,268,229],
"grape":[6.10,6.07,6.03,6.00,5.96,5.92],
"payout":[97,98,101,104,107,109]
},

"ファンキージャグラー2":{
"big":[273,270,266,254,240,229],
"reg":[439,399,331,290,268,229],
"grape":[6.14,6.10,6.05,6.02,5.98,5.95],
"payout":[97,98,101,104,107,109]
},

"ゴーゴージャグラー3":{
"big":[273,270,266,254,240,229],
"reg":[439,399,331,290,268,229],
"grape":[6.14,6.10,6.05,6.02,5.98,5.95],
"payout":[97,98,101,104,107,109]
}

}

machine = st.selectbox("機種", list(specs.keys()))

# ==============================
# セッション初期化
# ==============================

keys = [
"spin","big","reg","grape",
"investment","recovery",
"history","setting_history"
]

for k in keys:

    if k not in st.session_state:

        if k in ["history","setting_history"]:
            st.session_state[k] = []
        else:
            st.session_state[k] = 0


# ==============================
# 実戦カウンター
# ==============================

st.header("📱 実戦カウンター")

c1,c2,c3,c4 = st.columns(4)

with c1:

    if st.button("+10回転"):
        st.session_state.spin += 10

    if st.button("+100回転"):
        st.session_state.spin += 100


with c2:

    if st.button("🍇ぶどう"):
        st.session_state.grape += 1


with c3:

    if st.button("BIG"):
        st.session_state.big += 1


with c4:

    if st.button("REG"):
        st.session_state.reg += 1


spin = st.session_state.spin
big = st.session_state.big
reg = st.session_state.reg
grape = st.session_state.grape

st.write({
"回転":spin,
"BIG":big,
"REG":reg,
"ぶどう":grape
})

# ==============================
# 確率表示
# ==============================

st.header("📊 確率")

c1,c2,c3,c4 = st.columns(4)

with c1:

    if big>0:
        st.metric("BIG",f"1/{spin/big:.1f}")

with c2:

    if reg>0:
        st.metric("REG",f"1/{spin/reg:.1f}")

with c3:

    if big+reg>0:
        st.metric("合算",f"1/{spin/(big+reg):.1f}")

with c4:

    if grape>0:
        st.metric("ぶどう",f"1/{spin/grape:.2f}")


# ==============================
# ベイズAI
# ==============================

st.header("🤖 設定推測AI")


def bayes():

    results=[]

    for i in range(6):

        big_rate = 1/specs[machine]["big"][i]
        reg_rate = 1/specs[machine]["reg"][i]
        grape_rate = 1/specs[machine]["grape"][i]

        p_big = binom.pmf(big,spin,big_rate)
        p_reg = binom.pmf(reg,spin,reg_rate)
        p_grape = binom.pmf(grape,spin,grape_rate)

        likelihood = p_big*p_reg*p_grape

        results.append(likelihood)

    results = np.array(results)

    if results.sum()==0:
        return np.ones(6)/6

    return results/results.sum()


if spin>0:

    probs = bayes()

    df = pd.DataFrame({
        "設定":[1,2,3,4,5,6],
        "確率":probs
    })

    st.bar_chart(df.set_index("設定"))

    high = probs[3:].sum()

    st.metric("設定4以上確率",f"{high*100:.1f}%")


# ==============================
# 尤度スコア
# ==============================

st.header("📈 尤度スコア")


def likelihood():

    scores=[]

    for i in range(6):

        big_rate = 1/specs[machine]["big"][i]
        reg_rate = 1/specs[machine]["reg"][i]
        grape_rate = 1/specs[machine]["grape"][i]

        p_big = binom.pmf(big,spin,big_rate)
        p_reg = binom.pmf(reg,spin,reg_rate)
        p_grape = binom.pmf(grape,spin,grape_rate)

        score = np.log(p_big+1e-10)+np.log(p_reg+1e-10)+np.log(p_grape+1e-10)

        scores.append(score)

    return scores


scores = likelihood()

df2 = pd.DataFrame({
"設定":[1,2,3,4,5,6],
"尤度":scores
})

st.bar_chart(df2.set_index("設定"))


# ==============================
# 期待機械割
# ==============================

st.header("💰 期待機械割")

payout = np.array(specs[machine]["payout"])

ev = (probs*payout).sum()

st.metric("期待機械割",f"{ev:.2f}%")


# ==============================
# ヤメ時AI
# ==============================

st.header("🧠 ヤメ時AI")

if ev > 102:

    st.success("続行推奨")

elif ev > 100:

    st.warning("様子見")

else:

    st.error("ヤメ推奨")


# ==============================
# 投資管理
# ==============================

st.header("💸 投資")

c1,c2 = st.columns(2)

with c1:

    invest = st.number_input("投資",0,100000,st.session_state.investment)

    st.session_state.investment = invest

with c2:

    recovery = st.number_input("回収",0,100000,st.session_state.recovery)

    st.session_state.recovery = recovery

diff = recovery-invest

st.metric("差枚",diff)


# ==============================
# データ記録
# ==============================

if st.button("📈 データ記録"):

    st.session_state.history.append({
        "spin":spin,
        "reg":reg,
        "grape":grape
    })

    st.session_state.setting_history.append({
        "spin":spin,
        "setting":np.argmax(probs)+1
    })


# ==============================
# 推移グラフ
# ==============================

st.header("📊 推移")

hist = pd.DataFrame(st.session_state.history)

if len(hist)>0:

    hist["reg_prob"] = hist["spin"]/hist["reg"].replace(0,np.nan)

    fig = px.line(hist,x="spin",y="reg_prob")

    st.plotly_chart(fig,use_container_width=True)


# ==============================
# Google Sheets 保存
# ==============================

st.header("💾 クラウド保存")

if st.button("Sheets保存"):

    sheet = connect_sheet()

    if sheet:

        now = datetime.datetime.now()

        sheet.append_row([
            now.strftime("%Y-%m-%d %H:%M"),
            machine,
            spin,
            big,
            reg,
            grape,
            invest,
            recovery
        ])

        st.success("保存完了")

    else:

        st.error("Sheets接続失敗")


# ==============================
# ホール分析
# ==============================

st.header("🏪 ホール分析")

sheet = connect_sheet()

if sheet:

    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    st.dataframe(df)

    if "REG" in df.columns:

        df["REG確率"] = df["回転"]/df["REG"]

        st.bar_chart(df.groupby("機種")["REG確率"].mean())


# ==============================
# リセット
# ==============================

if st.button("🔄 リセット"):

    for k in keys:

        if k in ["history","setting_history"]:
            st.session_state[k]=[]
        else:
            st.session_state[k]=0

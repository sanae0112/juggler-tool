import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Juggler Analyzer", layout="wide")

# ======================
# ジャグラーデータ
# ======================

juggler_db = {

"アイムジャグラーEX":{"big":[273,269,269,259,259,255],"reg":[439,399,331,315,297,273],"grape":[6.02,6.02,6.02,6.02,6.02,5.78]},

"マイジャグラーV":{"big":[273,270,266,254,240,229],"reg":[439,399,331,315,297,273],"grape":[6.02,6.02,5.98,5.92,5.90,5.66]},

"ファンキージャグラー2":{"big":[270,267,260,254,240,229],"reg":[439,399,331,315,297,273],"grape":[6.05,6.01,5.98,5.92,5.88,5.83]},

"ゴーゴージャグラー3":{"big":[273,269,269,259,259,255],"reg":[439,399,331,315,297,273],"grape":[5.98,5.98,5.96,5.90,5.85,5.80]},

"ハッピージャグラーV3":{"big":[273,270,266,254,240,229],"reg":[439,399,331,315,297,273],"grape":[6.00,5.98,5.95,5.90,5.85,5.80]},

"ミスタージャグラー":{"big":[287,282,273,264,255,247],"reg":[455,431,366,336,305,273],"grape":[6.1,6.0,5.95,5.9,5.85,5.8]},

"ウルトラミラクルジャグラー":{"big":[287,282,273,264,255,247],"reg":[455,431,366,336,305,273],"grape":[6.1,6.0,5.95,5.9,5.85,5.8]},

"ジャグラーガールズSS":{"big":[287,282,273,264,255,247],"reg":[455,431,366,336,305,273],"grape":[6.1,6.0,5.95,5.9,5.85,5.8]}
}

# ======================
# Google Sheets接続
# ======================

def connect_sheet():

    scope=[
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
    ]

    creds=ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"],scope)

    client=gspread.authorize(creds)

    sheet=client.open("juggler_log").worksheet("log")

    return sheet

def save_to_sheet(data):

    sheet=connect_sheet()
    sheet.append_row(data)

# ======================
# セッション
# ======================

if "games" not in st.session_state:

    st.session_state.games=0
    st.session_state.big=0
    st.session_state.reg=0
    st.session_state.grape=0
    st.session_state.cherry=0

    st.session_state.big_t=0
    st.session_state.big_c=0
    st.session_state.big_rc=0

    st.session_state.reg_t=0
    st.session_state.reg_c=0
    st.session_state.reg_rc=0

    st.session_state.history=[]

# ======================
# サイドバー
# ======================

st.sidebar.title("🎰 Juggler Analyzer")

menu=st.sidebar.radio(

"モード",

[
"実戦カウンター",
"設定推測AI"
]

)

model=st.sidebar.selectbox("機種",list(juggler_db.keys()))
data=juggler_db[model]

# ======================
# 実戦カウンター
# ======================

if menu=="実戦カウンター":

    st.title("📱 実戦カウンター")

    col1,col2,col3=st.columns(3)

    if col1.button("1G"):
        st.session_state.games+=1

    if col2.button("🍇"):
        st.session_state.grape+=1

    if col3.button("🍒"):
        st.session_state.cherry+=1

    st.subheader("BIG内訳")

    col1,col2,col3=st.columns(3)

    if col1.button("単独BIG"):
        st.session_state.big+=1
        st.session_state.big_t+=1

    if col2.button("チェリーBIG"):
        st.session_state.big+=1
        st.session_state.big_c+=1

    if col3.button("レアチェBIG"):
        st.session_state.big+=1
        st.session_state.big_rc+=1

    st.subheader("REG内訳")

    col1,col2,col3=st.columns(3)

    if col1.button("単独REG"):
        st.session_state.reg+=1
        st.session_state.reg_t+=1

    if col2.button("チェリーREG"):
        st.session_state.reg+=1
        st.session_state.reg_c+=1

    if col3.button("レアチェREG"):
        st.session_state.reg+=1
        st.session_state.reg_rc+=1

    g=st.session_state.games
    b=st.session_state.big
    r=st.session_state.reg
    gr=st.session_state.grape
    ch=st.session_state.cherry

    st.write("回転数",g)

    if g>0:

        st.metric("合算",f"1/{round(g/max(b+r,1),1)}")
        st.metric("BIG",f"1/{round(g/max(b,1),1)}")
        st.metric("REG",f"1/{round(g/max(r,1),1)}")
        st.metric("ぶどう",f"1/{round(g/max(gr,1),2)}")
        st.metric("チェリー",f"1/{round(g/max(ch,1),2)}")

        st.session_state.history.append(
        {"games":g,"grape_rate":g/max(gr,1)}
        )

        df=pd.DataFrame(st.session_state.history)

        if len(df)>1:

            fig=px.line(df,x="games",y="grape_rate",title="🍇ぶどう推移")
            st.plotly_chart(fig)

    if st.button("💾 スプレッド保存"):

        save_to_sheet([

        str(pd.Timestamp.now()),
        model,
        g,
        b,
        r,
        gr,
        ch,
        st.session_state.big_t,
        st.session_state.big_c,
        st.session_state.big_rc,
        st.session_state.reg_t,
        st.session_state.reg_c,
        st.session_state.reg_rc

        ])

        st.success("保存しました")

# ======================
# AI設定推測
# ======================

elif menu=="設定推測AI":

    st.title("🤖 設定推測AI")

    games=st.number_input("ゲーム数",100,10000,3000)
    big=st.number_input("BIG",0,100,10)
    reg=st.number_input("REG",0,100,10)
    grape=st.number_input("ぶどう",0,2000,600)

    if st.button("解析"):

        bb_rate=games/max(big,1)
        reg_rate=games/max(reg,1)
        grape_rate=games/max(grape,1)

        scores=[]

        for i in range(6):

            diff=abs(bb_rate-data["big"][i]) \
            +abs(reg_rate-data["reg"][i]) \
            +abs(grape_rate-data["grape"][i])

            scores.append(1/(diff+1))

        prob=np.array(scores)/np.sum(scores)*100

        fig=px.bar(

        x=[f"設定{i+1}" for i in range(6)],
        y=prob,
        title="設定期待度"

        )

        st.plotly_chart(fig)

        st.metric("設定4以上",f"{prob[3]+prob[4]+prob[5]:.1f}%")

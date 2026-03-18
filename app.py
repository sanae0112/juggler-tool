import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO")

# ======================
# Google Sheets接続
# ======================
def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(creds)
    return client.open("juggler_data").sheet1

# ======================
# 入力
# ======================
machine = st.selectbox("機種", [
    "アイムジャグラーEX","マイジャグラーV","ファンキージャグラー2",
    "ゴーゴージャグラー3","ハッピージャグラーV3",
    "ミスタージャグラー","ジャグラーガールズSS","ウルトラミラクルジャグラー"
])

shop = st.text_input("ホール名")
machine_no = st.text_input("台番号")

if shop == "":
    st.stop()

spin = st.number_input("現在回転", 0)
prev_spin = st.number_input("前任者回転", 0)
total_spin = spin + prev_spin

grape = st.number_input("ぶどう", 0)
big = st.number_input("BIG", 0)
reg = st.number_input("REG", 0)

# ======================
# 信頼度
# ======================
confidence = min(total_spin / 3000, 1)
st.write("信頼度:", int(confidence * 100), "%")

# ======================
# 設定推測（優先順位）
# ======================
st.header("🎯設定推測")

priority_map = {
    "マイジャグラーV": ["reg","grape"],
    "アイムジャグラーEX": ["reg","grape"],
    "ファンキージャグラー2": ["grape","reg"],
    "ゴーゴージャグラー3": ["reg","grape"],
    "ハッピージャグラーV3": ["reg","grape"],
    "ミスタージャグラー": ["grape","reg"],
    "ジャグラーガールズSS": ["reg"],
    "ウルトラミラクルジャグラー": ["grape","reg"]
}

def get_weights(machine):
    priority = priority_map[machine]
    weights = {"reg":0,"grape":0}
    vals = [0.6,0.4]
    for i,k in enumerate(priority):
        weights[k] = vals[i]
    return weights

weights = get_weights(machine)

setting_data = {
    1: {"reg":439,"grape":6.1},
    2: {"reg":399,"grape":6.0},
    3: {"reg":331,"grape":5.9},
    4: {"reg":315,"grape":5.85},
    5: {"reg":290,"grape":5.8},
    6: {"reg":268,"grape":5.7},
}

def calc_score(a,b):
    return 1/(abs(a-b)+0.01)

scores = {}

if total_spin > 0 and reg > 0:

    for s,data in setting_data.items():
        score = 0

        # REG
        actual_reg = total_spin / reg
        score += calc_score(actual_reg,data["reg"]) * weights["reg"]

        # ぶどう
        if grape > 0:
            actual_grape = total_spin / grape
            score += calc_score(actual_grape,data["grape"]) * weights["grape"]

        scores[s] = score * confidence

    # ======================
    # 確率化
    # ======================
    total_score = sum(scores.values())
    probabilities = {s: scores[s]/total_score for s in scores}

    st.subheader("設定確率")

    for s in sorted(probabilities,key=probabilities.get,reverse=True):
        st.write(f"設定{s}: {round(probabilities[s]*100,1)}%")

    # グラフ
    fig = go.Figure()
    fig.add_bar(
        x=[f"設定{s}" for s in probabilities],
        y=[p*100 for p in probabilities.values()]
    )
    st.plotly_chart(fig,use_container_width=True)

# ======================
# 設定推移
# ======================
st.header("📈設定推移")

if total_spin > 1000 and reg > 0:

    chunk = 500
    x = []
    history = {i:[] for i in range(1,7)}

    for i in range(chunk,total_spin,chunk):
        ratio = i/total_spin
        r = max(1,int(reg*ratio))
        g = max(1,int(grape*ratio))

        x.append(i)

        for s,data in setting_data.items():
            sc = 0

            sc += calc_score(i/r,data["reg"]) * weights["reg"]
            sc += calc_score(i/g,data["grape"]) * weights["grape"]

            history[s].append(sc)

    fig = go.Figure()

    for s in history:
        fig.add_trace(go.Scatter(
            x=x,
            y=history[s],
            name=f"設定{s}",
            line=dict(width=4 if s==6 else 1)
        ))

    st.plotly_chart(fig,use_container_width=True)

# ======================
# 保存
# ======================
if st.button("保存"):
    sheet = connect_sheet()
    now = datetime.datetime.now()

    sheet.append_row([
        now.strftime("%Y-%m-%d %H:%M"),
        machine,shop,machine_no,
        spin,prev_spin,grape,big,reg
    ])

    st.success("保存完了")

# ======================
# 狙い台AI + イベント
# ======================
st.header("🤖狙い台AI")

target_date = st.date_input("日付", datetime.date.today())

if st.button("AI分析"):

    sheet = connect_sheet()
    df = pd.DataFrame(sheet.get_all_records())

    if len(df)>0:

        df["差枚"] = df["回収"] - df["投資"]
        df["日付"] = df["日時"].str[:10]
        df["日付_dt"] = pd.to_datetime(df["日付"])
        df["曜日"] = df["日付_dt"].dt.day_name()
        df["日"] = df["日付_dt"].dt.day

        # 直近
        recent = df[df["日付_dt"] > datetime.datetime.now()-datetime.timedelta(days=7)]

        # 曜日
        wd = target_date.strftime('%A')
        weekday_df = df[df["曜日"]==wd]

        gcols = ["ホール","機種","台番号"]

        r = recent.groupby(gcols)["差枚"].agg(["mean","count"])
        w = weekday_df.groupby(gcols)["差枚"].mean()

        merged = r.join(w,rsuffix="_wd").fillna(0).reset_index()

        merged["score"] = (
            merged["mean"]*0.5 +
            merged["mean_wd"]*0.3 +
            merged["count"]*50
        )

        # イベント補正
        day = target_date.day

        if day % 10 == 7:
            merged["score"] *= 1.2

        if day <=3 or day >=28:
            merged["score"] *= 1.1

        # 角台補正
        merged["num"] = merged["台番号"].astype(int)
        merged["corner"] = merged["num"] % 10

        merged["score"] *= merged["corner"].apply(
            lambda x: 1.2 if x in [0,1] else 1
        )

        top = merged.sort_values("score",ascending=False).head(10)

        st.dataframe(top)

        if len(top)>0:
            best = top.iloc[0]
            st.success(f"🔥最有力：{best['ホール']} {best['機種']} 台{best['台番号']}")

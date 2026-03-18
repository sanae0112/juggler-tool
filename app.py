import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO【Ver3 FINAL＋拡張】")

# ======================
# Google Sheets接続（機種ごと）
# ======================
def connect_sheet(machine_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open("juggler_data")

    try:
        sheet = spreadsheet.worksheet(machine_name)
    except:
        sheet = spreadsheet.add_worksheet(title=machine_name, rows="1000", cols="20")
        sheet.append_row([
            "日時","機種","ホール","台番号",
            "現在回転","前任者回転",
            "ぶどう","チェリー",
            "BIG","REG",
            "投資","回収"
        ])

    return sheet

# ======================
# がりぞう実戦値
# ======================
garizo_specs = {

"マイジャグラーV": {
    "weights": {"reg":0.4,"grape":0.3,"cherry_reg":0.3},
    "data": {
        1: {"reg":430,"grape":6.05,"cherry_reg":0.08},
        2: {"reg":390,"grape":6.00,"cherry_reg":0.09},
        3: {"reg":330,"grape":5.95,"cherry_reg":0.10},
        4: {"reg":305,"grape":5.85,"cherry_reg":0.11},
        5: {"reg":285,"grape":5.75,"cherry_reg":0.12},
        6: {"reg":265,"grape":5.65,"cherry_reg":0.14},
    }
},

"アイムジャグラーEX": {
    "weights": {"reg":0.45,"grape":0.35,"cherry_reg":0.2},
    "data": {
        1: {"reg":440,"grape":6.15,"cherry_reg":0.07},
        2: {"reg":400,"grape":6.05,"cherry_reg":0.08},
        3: {"reg":330,"grape":5.95,"cherry_reg":0.09},
        4: {"reg":310,"grape":5.90,"cherry_reg":0.10},
        5: {"reg":290,"grape":5.80,"cherry_reg":0.11},
        6: {"reg":270,"grape":5.75,"cherry_reg":0.13},
    }
},

"ミスタージャグラー": {
    "weights": {
        "grape":0.2,
        "pierrot":0.2,
        "bell":0.2,
        "cherry_big":0.15,
        "pierrot_big":0.15,
        "pierrot_reg":0.1
    },
    "data": {
        1: {"grape":6.2,"pierrot":7.5,"bell":10.5,"cherry_big":0.05,"pierrot_big":0.04,"pierrot_reg":0.03},
        2: {"grape":6.1,"pierrot":7.3,"bell":10.3,"cherry_big":0.06,"pierrot_big":0.05,"pierrot_reg":0.04},
        3: {"grape":6.0,"pierrot":7.1,"bell":10.0,"cherry_big":0.07,"pierrot_big":0.06,"pierrot_reg":0.05},
        4: {"grape":5.9,"pierrot":7.0,"bell":9.8,"cherry_big":0.08,"pierrot_big":0.07,"pierrot_reg":0.06},
        5: {"grape":5.85,"pierrot":6.9,"bell":9.5,"cherry_big":0.09,"pierrot_big":0.08,"pierrot_reg":0.07},
        6: {"grape":5.8,"pierrot":6.8,"bell":9.2,"cherry_big":0.10,"pierrot_big":0.09,"pierrot_reg":0.08},
    }
}
}

# ======================
# 入力
# ======================
machine = st.selectbox("機種", list(garizo_specs.keys()))
shop = st.text_input("ホール名")
machine_no = st.text_input("台番号")

spin = st.number_input("現在回転", 0)
prev_spin = st.number_input("前任者回転", 0)
total_spin = spin + prev_spin
st.write("総回転:", total_spin)

# チェリー
st.header("🍒チェリー")
cherry_free = st.number_input("フリー打ち", 0)
cherry_aim = st.number_input("狙い打ち", 0)
cherry = cherry_aim if cherry_aim > 0 else cherry_free

# ボーナス
st.header("🎰ボーナス")
big_single = st.number_input("単独BIG", 0)
big_cherry = st.number_input("チェリーBIG", 0)
big_rare = st.number_input("レアチェリーBIG", 0)
big_pierrot = st.number_input("ピエロBIG", 0)

reg_single = st.number_input("単独REG", 0)
reg_cherry = st.number_input("チェリーREG", 0)
reg_pierrot = st.number_input("ピエロREG", 0)

big_total = big_single + big_cherry + big_rare + big_pierrot
reg_total = reg_single + reg_cherry + reg_pierrot

# 小役
st.header("🍇小役")
grape = st.number_input("ぶどう", 0)
pierrot = st.number_input("ピエロ", 0)
bell = st.number_input("ベル", 0)

# ======================
# 設定推測
# ======================
def calc_score(a,b):
    return 1/(abs(a-b)+0.01)

spec = garizo_specs[machine]
confidence = min(total_spin / 4000, 1)

scores = {}

if total_spin > 0:

    for s in range(1,7):

        score = 0

        for key,weight in spec["weights"].items():

            if key == "reg" and reg_total > 0:
                score += calc_score(total_spin/reg_total, spec["data"][s]["reg"]) * weight

            if key == "grape" and grape > 0:
                score += calc_score(total_spin/grape, spec["data"][s]["grape"]) * weight

            if key == "cherry_reg" and cherry > 0:
                score += calc_score(reg_cherry/cherry, spec["data"][s]["cherry_reg"]) * weight

            if key == "cherry_big" and cherry > 0:
                score += calc_score(big_cherry/cherry, spec["data"][s]["cherry_big"]) * weight

            if key == "pierrot" and pierrot > 0:
                score += calc_score(total_spin/pierrot, spec["data"][s]["pierrot"]) * weight

            if key == "bell" and bell > 0:
                score += calc_score(total_spin/bell, spec["data"][s]["bell"]) * weight

            if key == "pierrot_big" and pierrot > 0:
                score += calc_score(big_pierrot/pierrot, spec["data"][s]["pierrot_big"]) * weight

            if key == "pierrot_reg" and pierrot > 0:
                score += calc_score(reg_pierrot/pierrot, spec["data"][s]["pierrot_reg"]) * weight

        score *= confidence
        score *= (1 + (confidence - 0.5) * 0.1)

        scores[s] = score

    total = sum(scores.values())
    probs = {s: scores[s]/total for s in scores}

    st.header("🎯設定推測")
    for s in sorted(probs, key=probs.get, reverse=True):
        st.write(f"設定{s}: {round(probs[s]*100,1)}%")

# ======================
# 設定推移
# ======================
st.header("📈設定推移")

if total_spin > 1000 and reg_total > 0:

    x = []
    history = {i:[] for i in range(1,7)}

    for i in range(500,total_spin,500):
        x.append(i)

        ratio = i / total_spin
        r = max(1,int(reg_total * ratio))
        g = max(1,int(grape * ratio))

        for s in range(1,7):
            sc = 0

            sc += calc_score(i/r, spec["data"][s].get("reg",999)) * spec["weights"].get("reg",0)
            sc += calc_score(i/g, spec["data"][s].get("grape",999)) * spec["weights"].get("grape",0)

            history[s].append(sc)

    fig = go.Figure()
    for s in history:
        fig.add_trace(go.Scatter(x=x,y=history[s],name=f"設定{s}"))

    st.plotly_chart(fig)

# ======================
# 複数台入力（追加）
# ======================
st.header("📥複数台データ入力")
multi_data = st.text_area(
    "CSV形式（台番号,現在回転,前任者回転,ぶどう,チェリー,BIG,REG,投資,回収）",
    height=150
)

# ======================
# 保存（拡張）
# ======================
st.header("💾保存")

investment = st.number_input("投資", 0)
recovery = st.number_input("回収", 0)

if st.button("保存"):
    sheet = connect_sheet(machine)
    now = datetime.datetime.now()

    rows = []

    # 単体
    rows.append([
        now.strftime("%Y-%m-%d %H:%M"),
        machine,shop,machine_no,
        spin,prev_spin,
        grape,cherry,
        big_total,reg_total,
        investment,recovery
    ])

    # 複数
    if multi_data:
        lines = multi_data.strip().split("\n")

        for line in lines:
            try:
                d = line.split(",")

                rows.append([
                    now.strftime("%Y-%m-%d %H:%M"),
                    machine,
                    shop,
                    d[0],
                    int(d[1]),
                    int(d[2]),
                    int(d[3]),
                    int(d[4]),
                    int(d[5]),
                    int(d[6]),
                    int(d[7]),
                    int(d[8])
                ])
            except:
                st.warning(f"入力エラー: {line}")

    for r in rows:
        sheet.append_row(r)

    st.success(f"{len(rows)}件 保存完了")

# ======================
# 履歴分析
# ======================
st.header("📊履歴分析")

if st.button("履歴読み込み"):

    sheet = connect_sheet(machine)
    df = pd.DataFrame(sheet.get_all_records())

    if len(df)>0:

        df["差枚"] = df["回収"] - df["投資"]

        st.dataframe(df)

        st.write("総収支:", df["差枚"].sum())
        st.write("勝率:", round(len(df[df["差枚"]>0])/len(df)*100,1), "%")

        df["日付"] = df["日時"].str[:10]
        st.bar_chart(df.groupby("日付")["差枚"].sum())

        df["月"] = df["日時"].str[:7]
        st.bar_chart(df.groupby("月")["差枚"].sum())

        st.bar_chart(df.groupby("ホール")["差枚"].sum())

# ======================
# 狙い台AI
# ======================
st.header("🤖狙い台AI")

target_date = st.date_input("日付", datetime.date.today())

if st.button("AI分析"):

    sheet = connect_sheet(machine)
    df = pd.DataFrame(sheet.get_all_records())

    if len(df)>0:

        df["差枚"] = df["回収"] - df["投資"]
        df["日付"] = df["日時"].str[:10]
        df["日付_dt"] = pd.to_datetime(df["日付"])
        df["曜日"] = df["日付_dt"].dt.day_name()

        recent = df[df["日付_dt"] > datetime.datetime.now()-datetime.timedelta(days=7)]
        weekday = df[df["曜日"] == target_date.strftime('%A')]

        g = ["ホール","台番号"]

        r = recent.groupby(g)["差枚"].agg(["mean","count"])
        w = weekday.groupby(g)["差枚"].mean()

        merged = r.join(w,rsuffix="_wd").fillna(0).reset_index()

        merged["score"] = merged["mean"]*0.5 + merged["mean_wd"]*0.3 + merged["count"]*50

        if target_date.day % 10 == 7:
            merged["score"] *= 1.2

        if target_date.day <= 3 or target_date.day >= 28:
            merged["score"] *= 1.1

        merged["num"] = merged["台番号"].astype(int)
        merged["score"] *= merged["num"].apply(lambda x:1.2 if x%10 in [0,1] else 1)

        top = merged.sort_values("score",ascending=False).head(10)

        st.dataframe(top)

        if len(top)>0:
            best = top.iloc[0]
            st.success(f"🔥最有力：{best['ホール']} 台{best['台番号']}")

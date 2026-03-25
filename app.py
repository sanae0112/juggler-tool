import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import re

st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO【上尾UNO】")

SHOP_NAME = "上尾UNO"
SPREADSHEET_NAME = "上尾UNO"

# =============================
# がりぞう実戦値
# =============================
garizo_specs = {
"マイジャグラーV":{
"weights":{"reg":0.4,"grape":0.3,"cherry_reg":0.3},
"data":{
1:{"reg":430,"grape":6.05,"cherry_reg":0.08},
2:{"reg":390,"grape":6.00,"cherry_reg":0.09},
3:{"reg":330,"grape":5.95,"cherry_reg":0.10},
4:{"reg":305,"grape":5.85,"cherry_reg":0.11},
5:{"reg":285,"grape":5.75,"cherry_reg":0.12},
6:{"reg":265,"grape":5.65,"cherry_reg":0.14}
}},
"アイムジャグラーEX":{
"weights":{"reg":0.5,"grape":0.3,"cherry_reg":0.2},
"data":{
1:{"reg":440,"grape":6.15,"cherry_reg":0.07},
2:{"reg":400,"grape":6.05,"cherry_reg":0.08},
3:{"reg":330,"grape":5.95,"cherry_reg":0.09},
4:{"reg":310,"grape":5.90,"cherry_reg":0.10},
5:{"reg":290,"grape":5.80,"cherry_reg":0.11},
6:{"reg":270,"grape":5.75,"cherry_reg":0.13}
}}
}

# =============================
# Google Sheets接続
# =============================
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    return client

def connect_sheet(sheet_name, headers=None):
    client = get_gspread_client()
    spreadsheet = client.open(SPREADSHEET_NAME)

    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="2000", cols="30")
        if headers:
            sheet.append_row(headers)
    return sheet

# =============================
# 評価関数
# =============================
def evaluate(spin,big,reg):
    if spin == 0 or (big+reg)==0:
        return "不明"
    reg_rate = spin/reg if reg>0 else 999
    combined = spin/(big+reg)
    if reg_rate < 280 and combined < 120:
        return "高"
    elif reg_rate < 330:
        return "中"
    else:
        return "低"

# =============================
# タブ
# =============================
tab1, tab2, tab3, tab4 = st.tabs(["①DMMコピペ", "②個人カウント", "③複数台入力", "④AI分析"])

# =============================
# ② 個人カウント（拡張版）
# =============================
with tab2:
    st.header("個人詳細データ")

    machine = st.selectbox("機種", list(garizo_specs.keys()))

    col1,col2,col3 = st.columns(3)

    with col1:
        machine_no = st.text_input("台番号")
        spin = st.number_input("現在回転",0)
        prev_spin = st.number_input("前任者回転",0)

    with col2:
        st.subheader("🍒チェリー")
        cherry_free = st.number_input("フリー打ちチェリー",0)
        cherry_aim = st.number_input("狙い打ちチェリー",0)
        cherry = cherry_aim if cherry_aim > 0 else cherry_free

        st.subheader("🍇小役")
        grape = st.number_input("ぶどう",0)
        pierrot = st.number_input("ピエロ",0)
        bell = st.number_input("ベル",0)

    with col3:
        st.subheader("🎰ボーナス内訳")
        big_single = st.number_input("単独BIG",0)
        big_cherry = st.number_input("チェリーBIG",0)
        reg_single = st.number_input("単独REG",0)
        reg_cherry = st.number_input("チェリーREG",0)

        invest = st.number_input("投資",0)
        collect = st.number_input("回収",0)

    big_total = big_single + big_cherry
    reg_total = reg_single + reg_cherry
    total_spin = spin + prev_spin

    st.write("総回転:", total_spin)

    # =============================
    # がりぞうAI設定推測
    # =============================
    if total_spin > 0 and reg_total > 0 and grape > 0:
        spec = garizo_specs[machine]
        weights = spec["weights"]
        data = spec["data"]

        scores = {}
        for setting in range(1,7):
            s = data[setting]
            score = 0

            reg_rate = total_spin / reg_total
            grape_rate = total_spin / grape
            cherry_reg_rate = reg_cherry / reg_total if reg_total>0 else 0

            score += weights["reg"] * abs(reg_rate - s["reg"])
            score += weights["grape"] * abs(grape_rate - s["grape"])
            score += weights["cherry_reg"] * abs(cherry_reg_rate - s["cherry_reg"])

            scores[setting] = score

        max_score = max(scores.values())
        probs = {k:(max_score-v) for k,v in scores.items()}
        total = sum(probs.values())
        probs = {k:round(v/total*100,1) for k,v in probs.items()}

        best = max(probs, key=probs.get)
        st.subheader(f"推定設定：設定{best}（{probs[best]}%）")

        fig = go.Figure(go.Bar(
            x=list(probs.values()),
            y=[f"設定{k}" for k in probs.keys()],
            orientation='h'
        ))
        st.plotly_chart(fig, use_container_width=True)

    # =============================
    # 保存
    # =============================
    if st.button("個人データ保存"):
        now = datetime.datetime.now()
        weekday = now.strftime("%A")
        eval_result = evaluate(total_spin,big_total,reg_total)

        headers = [
            "日時","曜日","機種","ホール","台番号",
            "回転","前任者回転","ぶどう","チェリー","ピエロ","ベル",
            "単独BIG","チェリーBIG","単独REG","チェリーREG",
            "投資","回収","評価"
        ]

        sheet = connect_sheet("個人データ", headers)

        sheet.append_row([
            now.strftime("%Y-%m-%d %H:%M"),
            weekday,
            machine,
            SHOP_NAME,
            machine_no,
            spin,
            prev_spin,
            grape,
            cherry,
            pierrot,
            bell,
            big_single,
            big_cherry,
            reg_single,
            reg_cherry,
            invest,
            collect,
            eval_result
        ])
        st.success("保存完了")

# =============================
# ④ AI分析
# =============================
with tab4:
    st.header("おすすめ台AI")

    sheet = connect_sheet("個人データ")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if len(df) > 0:
        score_map = {"高":2,"中":1,"低":-1}
        df["score"] = df["評価"].map(score_map)

        result = df.groupby("台番号")["score"].mean()
        best = result.idxmax()

        st.success(f"おすすめ台：{best}")

        fig = go.Figure(go.Bar(
            x=result.values,
            y=result.index,
            orientation='h'
        ))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("個人データがまだありません")

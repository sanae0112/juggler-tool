import streamlit as st
import pandas as pd
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

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )

    client = gspread.authorize(creds)
    return client.open("juggler_data").sheet1


# ======================
# 機種
# ======================
machine = st.selectbox("機種", [
    "アイムジャグラーEX",
    "マイジャグラーV",
    "ファンキージャグラー2",
    "ゴーゴージャグラー3",
    "ハッピージャグラーV3",
    "ミスタージャグラー",
    "ジャグラーガールズSS",
    "ウルトラミラクルジャグラー"
])

# ======================
# ホール
# ======================
shop = st.text_input("ホール名")
machine_no = st.text_input("台番号")

if shop == "":
    st.warning("ホール名を入力してください")
    st.stop()

# ======================
# 回転数
# ======================
spin = st.number_input("現在回転", 0)
prev_spin = st.number_input("前任者回転", 0)
total_spin = spin + prev_spin

st.write("総回転:", total_spin)

# ======================
# 前任者データ
# ======================
prev_big = st.number_input("前任者BIG", 0)
prev_reg = st.number_input("前任者REG", 0)
prev_diff = st.number_input("前任者差枚", 0)

# ======================
# チェリー入力方式
# ======================
st.header("🍒チェリー")

cherry_mode = st.radio("取得方法", ["狙い打ち", "フリー打ち"])
cherry = st.number_input("チェリー", 0)

miss_rate = 0.25
if cherry_mode == "フリー打ち":
    miss_rate = st.slider("取りこぼし率", 0.0, 0.5, 0.25)

if cherry_mode == "狙い打ち":
    cherry_corrected = cherry
else:
    cherry_corrected = cherry / (1 - miss_rate)

st.write("補正後チェリー:", int(cherry_corrected))

# ======================
# 小役
# ======================
grape = st.number_input("ぶどう", 0)

# ======================
# ボーナス
# ======================
big = st.number_input("BIG", 0)
reg = st.number_input("REG", 0)

# ======================
# ぶどう逆算（進化版）
# ======================
st.header("🍇ぶどう逆算（進化版）")

if prev_spin > 0:

    BIG_PAY = 240
    REG_PAY = 96
    GRAPE_PAY = 8
    CHERRY_PAY = 2

    grape_rate_table = {
        "アイムジャグラーEX": 6.0,
        "マイジャグラーV": 5.9,
        "ファンキージャグラー2": 5.8,
        "ゴーゴージャグラー3": 5.9,
        "ハッピージャグラーV3": 5.8,
        "ミスタージャグラー": 5.7,
        "ジャグラーガールズSS": 5.9,
        "ウルトラミラクルジャグラー": 5.8
    }

    bonus_out = (prev_big * BIG_PAY) + (prev_reg * REG_PAY)
    cherry_out = cherry_corrected * CHERRY_PAY

    remain = prev_diff - bonus_out - cherry_out

    grape_from_diff = remain / GRAPE_PAY
    theoretical = prev_spin / grape_rate_table[machine]

    grape_est = (grape_from_diff * 0.7) + (theoretical * 0.3)

    if grape_est < 0:
        grape_est = 0

    st.write("推定ぶどう:", int(grape_est))
    st.write("推定確率 1/", round(prev_spin / grape_est, 2))


# ======================
# 設定推測
# ======================
st.header("🎯設定推測")

setting_data = {
    1: {"reg": 439, "grape": 6.1},
    2: {"reg": 399, "grape": 6.0},
    3: {"reg": 331, "grape": 5.9},
    4: {"reg": 315, "grape": 5.85},
    5: {"reg": 290, "grape": 5.8},
    6: {"reg": 268, "grape": 5.7},
}

def calc_score(a, b):
    return 1 / (abs(a - b) + 0.01)

scores = {}

if total_spin > 0 and reg > 0:

    for s, data in setting_data.items():
        score = 0

        actual_reg = total_spin / reg
        score += calc_score(actual_reg, data["reg"]) * 0.5

        if grape > 0:
            actual_grape = total_spin / grape
            score += calc_score(actual_grape, data["grape"]) * 0.3

        scores[s] = score

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    for s, sc in sorted_scores:
        st.write(f"設定{s}: {round(sc,3)}")

# ======================
# 設定推移グラフ
# ======================
st.header("📈設定推移グラフ")

if total_spin > 1000 and reg > 0:

    chunk_size = 500
    x_axis = []
    history = {i: [] for i in range(1,7)}

    for i in range(chunk_size, total_spin, chunk_size):

        ratio = i / total_spin
        r = max(1, int(reg * ratio))
        g = max(1, int(grape * ratio))

        x_axis.append(i)

        for s, data in setting_data.items():

            score = 0

            actual_reg = i / r
            score += calc_score(actual_reg, data["reg"]) * 0.5

            actual_grape = i / g
            score += calc_score(actual_grape, data["grape"]) * 0.3

            history[s].append(score)

    fig = go.Figure()

    for s in history:
        fig.add_trace(go.Scatter(
            x=x_axis,
            y=history[s],
            mode='lines',
            name=f"設定{s}",
            line=dict(width=4 if s == 6 else 1)
        ))

    fig.update_layout(
        title="設定推移",
        xaxis_title="回転数",
        yaxis_title="スコア"
    )

    st.plotly_chart(fig, use_container_width=True)


# ======================
# 保存
# ======================
if st.button("保存"):

    sheet = connect_sheet()
    now = datetime.datetime.now()

    sheet.append_row([
        now.strftime("%Y-%m-%d %H:%M"),
        machine,
        shop,
        machine_no,
        spin,
        prev_spin,
        grape,
        cherry,
        big,
        reg
    ])

    st.success("保存完了")

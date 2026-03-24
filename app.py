import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =============================
# 基本設定
# =============================
st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO【完全版】")

SHOP_NAME = "上尾UNO"
DMM_JACKPOT_URL = "https://p-town.dmm.com/shops/saitama/3602/jackpot"
DISCORD_WEBHOOK_URL = "ここにDiscordWebhook"

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

# DMMシート（日別）
def connect_sheet():
    client = get_gspread_client()
    spreadsheet = client.open(SHOP_NAME)
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    try:
        sheet = spreadsheet.worksheet(today)
    except:
        sheet = spreadsheet.add_worksheet(title=today, rows="1000", cols="20")
        headers = [
            "台番","機種","回転数","BIG","REG","合算","REG確率",
            "差枚(DMM)","差枚(自分)","ぶどう","チェリー","設定推測","評価","メモ"
        ]
        sheet.append_row(headers)
    return sheet

# 個人データ
def connect_personal_sheet():
    client = get_gspread_client()
    spreadsheet = client.open(SHOP_NAME)

    try:
        sheet = spreadsheet.worksheet("個人データ")
    except:
        sheet = spreadsheet.add_worksheet(title="個人データ", rows="1000", cols="20")
        headers = [
            "日時","曜日","機種","ホール","台番号","回転","前任者回転",
            "ぶどう","チェリー","BIG","REG","投資","回収","メモ"
        ]
        sheet.append_row(headers)
    return sheet

# =============================
# DMMデータ取得
# =============================
def get_dmm_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(DMM_JACKPOT_URL, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    data = []
    rows = soup.select("table tr")

    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) >= 6:
            try:
                machine_no = cols[0].text.strip()
                machine_name = cols[1].text.strip()
                big = int(cols[2].text.strip())
                reg = int(cols[3].text.strip())
                spin = int(cols[4].text.strip().replace(",", ""))
                diff = int(cols[5].text.strip().replace(",", ""))

                gassan = spin / (big + reg) if (big + reg) > 0 else 0
                reg_prob = spin / reg if reg > 0 else 0

                data.append([
                    machine_no, machine_name, spin, big, reg,
                    round(gassan, 1), round(reg_prob, 1), diff
                ])
            except:
                pass

    return pd.DataFrame(data, columns=[
        "台番","機種","回転数","BIG","REG","合算","REG確率","差枚(DMM)"
    ])

# =============================
# スコア計算
# =============================
def calculate_score(row):
    score = 0

    if row["REG確率"] <= 250:
        score += 50
    elif row["REG確率"] <= 300:
        score += 30
    elif row["REG確率"] <= 350:
        score += 10

    if row["合算"] <= 120:
        score += 30
    elif row["合算"] <= 140:
        score += 20
    elif row["合算"] <= 160:
        score += 10

    if row["差枚(DMM)"] > 2000:
        score += 20
    elif row["差枚(DMM)"] > 1000:
        score += 10

    return score

# =============================
# Discord通知
# =============================
def send_discord(message):
    payload = {"content": message}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

# =============================
# DMM取得UI
# =============================
st.header("📊 DMMデータ取得")

if st.button("DMMデータ取得"):
    df = get_dmm_data()
    sheet = connect_sheet()

    for i, row in df.iterrows():
        sheet.append_row(row.tolist())

    st.success("DMMデータ保存完了")

    df["スコア"] = df.apply(calculate_score, axis=1)
    ranking = df.sort_values("スコア", ascending=False).head(10)

    st.subheader("おすすめ台ランキング")
    st.dataframe(ranking)

    message = "【おすすめ台ランキング】\n"
    for i, row in ranking.iterrows():
        message += f"台{row['台番']} {row['機種']} スコア{row['スコア']} 差枚{row['差枚(DMM)']}\n"

    send_discord(message)
    st.success("Discord送信完了")

# =============================
# 個人データ入力
# =============================
st.header("✍ 個人データ入力")

col1, col2, col3 = st.columns(3)

with col1:
    machine = st.text_input("機種")
    machine_no = st.number_input("台番号", 1, 1000)
    spin = st.number_input("回転数", 0, 10000)

with col2:
    big = st.number_input("BIG", 0, 100)
    reg = st.number_input("REG", 0, 100)
    budo = st.number_input("ぶどう", 0, 2000)
    cherry = st.number_input("チェリー", 0, 500)

with col3:
    invest = st.number_input("投資", 0, 100000)
    collect = st.number_input("回収", 0, 100000)
    memo = st.text_input("メモ")

if st.button("個人データ保存"):
    now = datetime.datetime.now()
    sheet = connect_personal_sheet()

    data = [
        now.strftime("%Y-%m-%d %H:%M"),
        now.strftime("%A"),
        machine,
        SHOP_NAME,
        machine_no,
        spin,
        0,
        budo,
        cherry,
        big,
        reg,
        invest,
        collect,
        memo
    ]

    sheet.append_row(data)
    st.success("保存完了")

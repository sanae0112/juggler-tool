import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO【Ver5】")

# ======================
# Google Sheets接続（日付保存）
# ======================
def connect_sheet_date(machine_name, mode, date):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open("juggler_data")

    sheet_name = f"{date}_{machine_name}_{mode}"

    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="2000", cols="30")
        sheet.append_row([
            "日時","曜日","機種","ホール","台番号",
            "総回転","前任者回転",
            "ぶどう","チェリー","ピエロ","ベル",
            "単独BIG","チェリーBIG","レアチェリーBIG","ピエロBIG",
            "単独REG","チェリーREG","ピエロREG",
            "BIG合算","REG合算",
            "投資","回収","差枚","評価"
        ])
    return sheet

# ======================
# 日付選択（6日前まで）
# ======================
st.header("📅 保存日選択")

today = datetime.date.today()
date_list = [today - datetime.timedelta(days=i) for i in range(7)]
date_str_list = [d.strftime("%Y-%m-%d") for d in date_list]

save_date = st.selectbox("保存する日付", date_str_list)

# ======================
# 機種
# ======================
machine_list = [
    "マイジャグラーV",
    "アイムジャグラーEX",
    "ファンキージャグラー2",
    "ゴーゴージャグラー3",
    "ハッピージャグラーV III",
    "ジャグラーガールズSS",
    "ミスタージャグラー",
    "ウルトラミラクルジャグラー"
]

# ======================
# 基本情報
# ======================
st.header("📥 基本情報")

col1, col2, col3 = st.columns(3)

machine = col1.selectbox("機種", machine_list)
shop = col2.text_input("ホール名")
machine_no = col3.text_input("台番号")

spin = st.number_input("現在回転", 0)
prev_spin = st.number_input("前任者回転", 0)
total_spin = spin + prev_spin

st.write("総回転:", total_spin)

# ======================
# チェリー
# ======================
st.header("🍒チェリー")

cherry_free = st.number_input("フリー打ち", 0)
cherry_aim = st.number_input("狙い打ち", 0)
cherry = cherry_aim if cherry_aim > 0 else cherry_free

# ======================
# ボーナス内訳
# ======================
st.header("🎰ボーナス内訳")

big_single = st.number_input("単独BIG", 0)
big_cherry = st.number_input("チェリーBIG", 0)
big_rare = st.number_input("レアチェリーBIG", 0)
big_pierrot = st.number_input("ピエロBIG", 0)

reg_single = st.number_input("単独REG", 0)
reg_cherry = st.number_input("チェリーREG", 0)
reg_pierrot = st.number_input("ピエロREG", 0)

big_total = big_single + big_cherry + big_rare + big_pierrot
reg_total = reg_single + reg_cherry + reg_pierrot

st.write("BIG合計:", big_total)
st.write("REG合計:", reg_total)

# ======================
# 小役
# ======================
st.header("🍇小役")

grape = st.number_input("ぶどう", 0)
pierrot = st.number_input("ピエロ", 0)
bell = st.number_input("ベル", 0)

# ======================
# 収支
# ======================
st.header("💰収支")

invest = st.number_input("投資", 0)
collect = st.number_input("回収", 0)
coin = collect - invest

st.write("差枚:", coin)

# ======================
# 評価
# ======================
def evaluate(spin, big, reg):
    if spin == 0 or (big+reg) == 0:
        return "不明"

    reg_rate = spin / reg if reg > 0 else 999
    combined = spin / (big + reg)

    if reg_rate < 280 and combined < 120:
        return "高"
    elif reg_rate < 330:
        return "中"
    else:
        return "低"

# ======================
# 保存
# ======================
st.header("💾 保存")

col1, col2 = st.columns(2)

if col1.button("🟢 自分データ保存"):
    weekday = datetime.datetime.strptime(save_date, "%Y-%m-%d").strftime("%A")
    eval_result = evaluate(total_spin, big_total, reg_total)

    sheet = connect_sheet_date(machine, "自分", save_date)
    sheet.append_row([
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        weekday,
        machine,
        shop,
        machine_no,
        total_spin,
        prev_spin,
        grape,
        cherry,
        pierrot,
        bell,
        big_single,
        big_cherry,
        big_rare,
        big_pierrot,
        reg_single,
        reg_cherry,
        reg_pierrot,
        big_total,
        reg_total,
        invest,
        collect,
        coin,
        eval_result
    ])
    st.success("保存完了")

if col2.button("🔵 他人データ保存"):
    weekday = datetime.datetime.strptime(save_date, "%Y-%m-%d").strftime("%A")
    eval_result = evaluate(total_spin, big_total, reg_total)

    sheet = connect_sheet_date(machine, "他人", save_date)
    sheet.append_row([
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        weekday,
        machine,
        shop,
        machine_no,
        total_spin,
        prev_spin,
        grape,
        cherry,
        pierrot,
        bell,
        big_single,
        big_cherry,
        big_rare,
        big_pierrot,
        reg_single,
        reg_cherry,
        reg_pierrot,
        big_total,
        reg_total,
        invest,
        collect,
        coin,
        eval_result
    ])
    st.success("保存完了")

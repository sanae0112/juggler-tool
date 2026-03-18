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
# 追加：シート分岐
# ======================
def connect_sheet_mode(machine_name, mode):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open("juggler_data")

    sheet_name = f"{machine_name}_{mode}"

    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="2000", cols="20")
        sheet.append_row([
            "日時","機種","ホール","台番号",
            "現在回転","前任者回転",
            "ぶどう","チェリー",
            "BIG","REG",
            "投資","回収"
        ])
    return sheet

# ======================
# CSS
# ======================
st.markdown("""
<style>
.green-btn button {background-color:#28a745!important;color:white!important;}
.blue-btn button {background-color:#007bff!important;color:white!important;}
</style>
""", unsafe_allow_html=True)

# ======================
# 表示・色ロジック（改良追加）
# ======================
def fmt(v):
    return f"{v:,.1f}" if v else "-"

def col(v):
    if v is None:
        return "gray"
    elif v < 270:
        return "red"
    elif v < 300:
        return "orange"
    elif v < 350:
        return "blue"
    else:
        return "gray"

# ======================
# がりぞう実戦値（全機種）
# ======================
garizo_specs = {
"マイジャグラーV":{"weights":{"reg":0.4,"grape":0.3,"cherry_reg":0.3},
"data":{1:{"reg":430,"grape":6.05,"cherry_reg":0.08},2:{"reg":390,"grape":6.00,"cherry_reg":0.09},
3:{"reg":330,"grape":5.95,"cherry_reg":0.10},4:{"reg":305,"grape":5.85,"cherry_reg":0.11},
5:{"reg":285,"grape":5.75,"cherry_reg":0.12},6:{"reg":265,"grape":5.65,"cherry_reg":0.14}}},

"アイムジャグラーEX":{"weights":{"reg":0.45,"grape":0.35,"cherry_reg":0.2},
"data":{1:{"reg":440,"grape":6.15,"cherry_reg":0.07},2:{"reg":400,"grape":6.05,"cherry_reg":0.08},
3:{"reg":330,"grape":5.95,"cherry_reg":0.09},4:{"reg":310,"grape":5.90,"cherry_reg":0.10},
5:{"reg":290,"grape":5.80,"cherry_reg":0.11},6:{"reg":270,"grape":5.75,"cherry_reg":0.13}}},

"ミスタージャグラー":{"weights":{"grape":0.2,"pierrot":0.2,"bell":0.2,"cherry_big":0.15,"pierrot_big":0.15,"pierrot_reg":0.1},
"data":{1:{"grape":6.2,"pierrot":7.5,"bell":10.5,"cherry_big":0.05,"pierrot_big":0.04,"pierrot_reg":0.03},
2:{"grape":6.1,"pierrot":7.3,"bell":10.3,"cherry_big":0.06,"pierrot_big":0.05,"pierrot_reg":0.04},
3:{"grape":6.0,"pierrot":7.1,"bell":10.0,"cherry_big":0.07,"pierrot_big":0.06,"pierrot_reg":0.05},
4:{"grape":5.9,"pierrot":7.0,"bell":9.8,"cherry_big":0.08,"pierrot_big":0.07,"pierrot_reg":0.06},
5:{"grape":5.85,"pierrot":6.9,"bell":9.5,"cherry_big":0.09,"pierrot_big":0.08,"pierrot_reg":0.07},
6:{"grape":5.8,"pierrot":6.8,"bell":9.2,"cherry_big":0.10,"pierrot_big":0.09,"pierrot_reg":0.08}}},

"ファンキージャグラー2":{"weights":{"reg":0.4,"grape":0.4,"cherry_reg":0.2},
"data":{1:{"reg":430,"grape":6.10,"cherry_reg":0.08},2:{"reg":400,"grape":6.05,"cherry_reg":0.09},
3:{"reg":340,"grape":6.00,"cherry_reg":0.10},4:{"reg":310,"grape":5.90,"cherry_reg":0.11},
5:{"reg":290,"grape":5.85,"cherry_reg":0.12},6:{"reg":270,"grape":5.80,"cherry_reg":0.13}}},

"ゴーゴージャグラー3":{"weights":{"reg":0.45,"grape":0.35,"cherry_reg":0.2},
"data":{1:{"reg":430,"grape":6.10,"cherry_reg":0.08},2:{"reg":390,"grape":6.05,"cherry_reg":0.09},
3:{"reg":330,"grape":5.95,"cherry_reg":0.10},4:{"reg":305,"grape":5.90,"cherry_reg":0.11},
5:{"reg":285,"grape":5.85,"cherry_reg":0.12},6:{"reg":265,"grape":5.80,"cherry_reg":0.13}}},

"ハッピージャグラーV III":{"weights":{"reg":0.45,"grape":0.35,"cherry_reg":0.2},
"data":{1:{"reg":430,"grape":6.10,"cherry_reg":0.08},2:{"reg":400,"grape":6.05,"cherry_reg":0.09},
3:{"reg":330,"grape":5.95,"cherry_reg":0.10},4:{"reg":305,"grape":5.90,"cherry_reg":0.11},
5:{"reg":285,"grape":5.85,"cherry_reg":0.12},6:{"reg":265,"grape":5.80,"cherry_reg":0.13}}},

"ジャグラーガールズSS":{"weights":{"reg":0.45,"grape":0.35,"cherry_reg":0.2},
"data":{1:{"reg":430,"grape":6.10,"cherry_reg":0.08},2:{"reg":390,"grape":6.05,"cherry_reg":0.09},
3:{"reg":330,"grape":5.95,"cherry_reg":0.10},4:{"reg":305,"grape":5.90,"cherry_reg":0.11},
5:{"reg":285,"grape":5.85,"cherry_reg":0.12},6:{"reg":265,"grape":5.80,"cherry_reg":0.13}}},

"ウルトラミラクルジャグラー":{"weights":{"grape":0.2,"pierrot":0.2,"bell":0.2,"cherry_big":0.15,"pierrot_big":0.15,"pierrot_reg":0.1},
"data":{1:{"grape":6.2,"pierrot":7.5,"bell":10.5,"cherry_big":0.05,"pierrot_big":0.04,"pierrot_reg":0.03},
2:{"grape":6.1,"pierrot":7.3,"bell":10.3,"cherry_big":0.06,"pierrot_big":0.05,"pierrot_reg":0.04},
3:{"grape":6.0,"pierrot":7.1,"bell":10.0,"cherry_big":0.07,"pierrot_big":0.06,"pierrot_reg":0.05},
4:{"grape":5.9,"pierrot":7.0,"bell":9.8,"cherry_big":0.08,"pierrot_big":0.07,"pierrot_reg":0.06},
5:{"grape":5.85,"pierrot":6.9,"bell":9.5,"cherry_big":0.09,"pierrot_big":0.08,"pierrot_reg":0.07},
6:{"grape":5.8,"pierrot":6.8,"bell":9.2,"cherry_big":0.10,"pierrot_big":0.09,"pierrot_reg":0.08}}}
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

# ======================
# 複数台UI
# ======================
st.header("📥追加：複数台入力")

if "multi_rows" not in st.session_state:
    st.session_state.multi_rows = []

if st.button("➕ 台を追加"):
    st.session_state.multi_rows.append({})

for i, row in enumerate(st.session_state.multi_rows):

    c0,c1,c2,c3,c4,c5 = st.columns(6)

    row["機種"] = c0.selectbox("機種", list(garizo_specs.keys()), key=f"mm{i}")
    row["台番号"] = c1.text_input("台番号", key=f"mno{i}")
    row["回転"] = c2.number_input("回転", key=f"msp{i}")
    row["BIG"] = c3.number_input("BIG", key=f"mb{i}")
    row["REG"] = c4.number_input("REG", key=f"mr{i}")
    row["差枚"] = c5.number_input("差枚", key=f"md{i}")

    big_p = row["回転"]/row["BIG"] if row["BIG"] > 0 else None
    reg_p = row["回転"]/row["REG"] if row["REG"] > 0 else None

    st.markdown(f"""
    BIG確率: <span style='color:{col(big_p)}'>{fmt(big_p)}</span>
    REG確率: <span style='color:{col(reg_p)}'>{fmt(reg_p)}</span>
    """, unsafe_allow_html=True)

# ======================
# 保存
# ======================
st.header("💾複数台データ保存")

c1, c2 = st.columns(2)

with c1:
    if st.button("🟢 複数台を自分データとして保存"):
        now = datetime.datetime.now()
        count = 0
        for row in st.session_state.multi_rows:
            if row.get("台番号","") == "" or not row.get("機種"):
                continue
            sheet = connect_sheet_mode(row["機種"], "自分")
            sheet.append_row([
                now.strftime("%Y-%m-%d %H:%M"),
                row["機種"], shop, row["台番号"],
                row["回転"], 0, 0, 0,
                row["BIG"], row["REG"],
                0, row["差枚"]
            ])
            count += 1
        st.success(f"{count}台 保存完了")

with c2:
    if st.button("🔵 複数台を他人データとして保存"):
        now = datetime.datetime.now()
        count = 0
        for row in st.session_state.multi_rows:
            if row.get("台番号","") == "" or not row.get("機種"):
                continue
            sheet = connect_sheet_mode(row["機種"], "他人")
            sheet.append_row([
                now.strftime("%Y-%m-%d %H:%M"),
                row["機種"], shop, row["台番号"],
                row["回転"], 0, 0, 0,
                row["BIG"], row["REG"],
                0, row["差枚"]
            ])
            count += 1
        st.success(f"{count}台 保存完了")

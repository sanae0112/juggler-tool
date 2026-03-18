import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ======================
# 画面設定
# ======================
st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO【完全版】")

# ======================
# Google Sheets接続
# ======================
def connect_sheet(name):
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
        sheet = spreadsheet.worksheet(name)
    except:
        sheet = spreadsheet.add_worksheet(title=name, rows="2000", cols="20")
        sheet.append_row([
            "日時","機種","ホール","台番号",
            "総回転","BIG","REG","差枚",
            "BIG確率","REG確率"
        ])
    return sheet

# ======================
# CSS（色分け）
# ======================
st.markdown("""
<style>
.green-btn button {background-color:#28a745!important;color:white!important;}
.blue-btn button {background-color:#007bff!important;color:white!important;}
</style>
""", unsafe_allow_html=True)

# ======================
# 現行ジャグラー全機種
# ======================
machines = [
"マイジャグラーV",
"アイムジャグラーEX",
"ミスタージャグラー",
"ファンキージャグラー2",
"ゴーゴージャグラー3",
"ハッピージャグラーV III",
"ジャグラーガールズSS",
"ウルトラミラクルジャグラー"
]

# ======================
# 単体入力
# ======================
st.header("■ 単体データ入力")

machine = st.selectbox("機種", machines)
shop = st.text_input("ホール名")
machine_no = st.text_input("台番号")

total_spin = st.number_input("総回転数", 0)
big = st.number_input("BIG回数", 0)
reg = st.number_input("REG回数", 0)
diff = st.number_input("差枚数", 0)

# ======================
# 計算
# ======================
big_prob = total_spin / big if big > 0 else 0
reg_prob = total_spin / reg if reg > 0 else 0

st.subheader("■ 結果")

col1, col2 = st.columns(2)

with col1:
    st.metric("BIG確率", f"1/{int(big_prob) if big_prob else 0}")

with col2:
    st.metric("REG確率", f"1/{int(reg_prob) if reg_prob else 0}")

# ======================
# 保存
# ======================
col1, col2 = st.columns(2)

with col1:
    if st.button("🟢 自分データ保存"):
        sheet = connect_sheet(f"{machine}_自分")
        sheet.append_row([
            str(datetime.datetime.now()),
            machine, shop, machine_no,
            total_spin, big, reg, diff,
            big_prob, reg_prob
        ])
        st.success("自分データ保存完了")

with col2:
    if st.button("🔵 機種データ保存"):
        sheet = connect_sheet(machine)
        sheet.append_row([
            str(datetime.datetime.now()),
            machine, shop, machine_no,
            total_spin, big, reg, diff,
            big_prob, reg_prob
        ])
        st.success("機種データ保存完了")

# ======================
# 複数台入力
# ======================
st.header("■ 複数台入力（島分析）")

multi_data = []

for i in range(5):
    st.subheader(f"{i+1}台目")

    m = st.selectbox(f"機種{i}", machines, key=f"m{i}")
    spin = st.number_input(f"回転{i}", 0, key=f"s{i}")
    b = st.number_input(f"BIG{i}", 0, key=f"b{i}")
    r = st.number_input(f"REG{i}", 0, key=f"r{i}")
    d = st.number_input(f"差枚{i}", 0, key=f"d{i}")

    if spin > 0:
        multi_data.append([m, spin, b, r, d])

# ======================
# 複数台保存
# ======================
if st.button("複数台保存"):
    for data in multi_data:
        m, spin, b, r, d = data

        bp = spin / b if b > 0 else 0
        rp = spin / r if r > 0 else 0

        sheet = connect_sheet(m)

        sheet.append_row([
            str(datetime.datetime.now()),
            m, shop, "複数",
            spin, b, r, d,
            bp, rp
        ])

    st.success("複数台保存完了")

# ======================
# 簡易グラフ
# ======================
st.header("■ データ可視化")

if st.button("グラフ表示"):
    try:
        sheet = connect_sheet(machine)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            y=df["差枚"],
            mode="lines+markers",
            name="差枚推移"
        ))

        st.plotly_chart(fig, use_container_width=True)

    except:
        st.warning("データなし")

# ======================
# AI風コメント
# ======================
st.header("■ AI分析")

if total_spin > 0:
    if reg_prob != 0 and reg_prob < 270:
        st.success("高設定期待度 高")
    elif reg_prob != 0 and reg_prob < 320:
        st.warning("中間設定の可能性")
    else:
        st.error("低設定の可能性大")

# ======================
# 完了
# ======================
st.write("✔ 完全版稼働中")

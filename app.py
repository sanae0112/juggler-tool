# app.py
import streamlit as st
import pandas as pd
import datetime
import gspread
import time
import re
import plotly.graph_objects as go
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import WorksheetNotFound

# ==================================================
# 基本設定
# ==================================================
st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO【上尾UNO】")

SHOP_NAME = "上尾UNO"
SPREADSHEET_NAME = "上尾UNO"

machine_list = [
    "マイジャグラーV",
    "ネオアイムジャグラー",
    "ファンキージャグラー2",
    "ゴージャグラー3",
    "ハッピージャグラーV3",
    "ミスタージャグラー",
    "ジャグラーガールズ",
    "ウルトラミラクルジャグラー"
]

# ==================================================
# Google Sheets 接続安定版
# ==================================================
@st.cache_resource
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, scope
    )
    client = gspread.authorize(credentials)
    return client


def connect_sheet(sheet_name, headers=None):
    client = get_gspread_client()
    spreadsheet = client.open(SPREADSHEET_NAME)

    for _ in range(3):
        try:
            sheet = spreadsheet.worksheet(sheet_name)
            return sheet
        except WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(
                title=sheet_name,
                rows="3000",
                cols="30"
            )
            if headers:
                sheet.append_row(headers)
            return sheet
        except:
            time.sleep(1)

    st.error("Google Sheets接続失敗")
    st.stop()


# ==================================================
# 評価
# ==================================================
def evaluate(spin, big, reg):
    if spin == 0 or (big + reg) == 0:
        return "不明"

    reg_rate = spin / reg if reg > 0 else 999
    combined = spin / (big + reg)

    if reg_rate < 280 and combined < 120:
        return "高"
    elif reg_rate < 330:
        return "中"
    else:
        return "低"


# ==================================================
# タブ
# ==================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["①DMMコピペ", "②個人カウント", "③複数台入力", "④ホール分析AI"]
)

# ==================================================
# ① DMMコピペ保存（10日前まで）
# ==================================================
with tab1:
    st.header("DMMコピペ保存（本日〜10日前）")

    machine_name = st.selectbox("機種選択", machine_list)
    paste_data = st.text_area("DMM表貼り付け")

    if st.button("コピペデータ保存"):

        lines = paste_data.split("\n")
        today = datetime.date.today()
        target_date = today
        data_by_date = {}

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if "本日" in line:
                target_date = today
                continue

            elif "日前" in line:
                m = re.search(r"(\d+)日前", line)

                if m:
                    num = int(m.group(1))

                    if num > 10:
                        continue

                    target_date = today - datetime.timedelta(days=num)
                continue

            nums = re.findall(r"-?\d+", line)

            if len(nums) >= 5:
                try:
                    machine_no = nums[0]
                    big = int(nums[1])
                    reg = int(nums[2])
                    spin = int(nums[3])
                    diff = int(nums[4])

                    total_bonus = big + reg
                    gassan = round(spin / total_bonus, 1) if total_bonus else 0
                    reg_prob = round(spin / reg, 1) if reg > 0 else 0

                    date_str = target_date.strftime("%Y-%m-%d")

                    if date_str not in data_by_date:
                        data_by_date[date_str] = []

                    data_by_date[date_str].append([
                        machine_no,
                        machine_name,
                        spin,
                        big,
                        reg,
                        gassan,
                        reg_prob,
                        diff
                    ])
                except:
                    pass

        for date_str, rows in data_by_date.items():

            headers = [
                "台番", "機種", "回転数", "BIG", "REG",
                "合算", "REG確率", "差枚"
            ]

            df = pd.DataFrame(rows, columns=headers)

            sheet = connect_sheet(date_str, headers)

            values = df.values.tolist()

            if values:
                sheet.append_rows(values)

        st.success("本日〜10日前まで保存完了")


# ==================================================
# ② 個人詳細データ
# ==================================================
with tab2:
    st.header("個人詳細データ")

    machine = st.selectbox("機種", machine_list, key="solo_machine")

    col1, col2, col3 = st.columns(3)

    with col1:
        machine_no = st.text_input("台番号")
        spin = st.number_input("現在回転", 0)
        prev_spin = st.number_input("前任者回転", 0)

    st.subheader("🍒チェリー")
    cherry_free = st.number_input("フリー打ち", 0)
    cherry_aim = st.number_input("狙い打ち", 0)

    cherry = cherry_aim if cherry_aim > 0 else cherry_free

    st.subheader("🎰ボーナス")

    big_single = st.number_input("単独BIG", 0)
    big_cherry = st.number_input("チェリーBIG", 0)
    big_rare = st.number_input("レアチェリーBIG", 0)
    big_pierrot = st.number_input("ピエロBIG", 0)

    reg_single = st.number_input("単独REG", 0)
    reg_cherry = st.number_input("チェリーREG", 0)
    reg_pierrot = st.number_input("ピエロREG", 0)

    big_total = big_single + big_cherry + big_rare + big_pierrot
    reg_total = reg_single + reg_cherry + reg_pierrot

    st.subheader("🍇小役")

    grape = st.number_input("ぶどう", 0)
    pierrot = st.number_input("ピエロ", 0)
    bell = st.number_input("ベル", 0)

    st.subheader("💰収支")

    invest = st.number_input("投資", 0)
    collect = st.number_input("回収", 0)

    total_spin = spin + prev_spin

    st.write("総回転:", total_spin)

    if total_spin > 0:
        if big_total > 0:
            st.write("BIG確率:", round(total_spin / big_total, 1))
        if reg_total > 0:
            st.write("REG確率:", round(total_spin / reg_total, 1))
        if big_total + reg_total > 0:
            st.write("合算:", round(total_spin / (big_total + reg_total), 1))
        if grape > 0:
            st.write("ぶどう確率:", round(total_spin / grape, 2))

    if st.button("個人データ保存"):

        now = datetime.datetime.now()

        headers = [
            "日時", "曜日", "機種", "ホール", "台番号",
            "回転", "前任者回転", "ぶどう", "チェリー",
            "BIG", "REG", "投資", "回収", "評価"
        ]

        sheet = connect_sheet("個人データ", headers)

        sheet.append_row([
            now.strftime("%Y-%m-%d %H:%M"),
            now.strftime("%A"),
            machine,
            SHOP_NAME,
            machine_no,
            spin,
            prev_spin,
            grape,
            cherry,
            big_total,
            reg_total,
            invest,
            collect,
            evaluate(total_spin, big_total, reg_total)
        ])

        st.success("保存完了")


# ==================================================
# ③ 複数台入力
# ==================================================
with tab3:
    st.header("複数台入力（他人データ）")

    if "rows" not in st.session_state:
        st.session_state.rows = []

    if st.button("台追加"):
        st.session_state.rows.append({})

    for i in range(len(st.session_state.rows)):
        c1, c2, c3, c4, c5, c6 = st.columns(6)

        row = {}

        row["機種"] = c1.selectbox(
            "機種", machine_list, key=f"m{i}"
        )
        row["台番号"] = c2.text_input("台番号", key=f"n{i}")
        row["回転"] = c3.number_input("回転", 0, key=f"s{i}")
        row["BIG"] = c4.number_input("BIG", 0, key=f"b{i}")
        row["REG"] = c5.number_input("REG", 0, key=f"r{i}")
        row["差枚"] = c6.number_input("差枚", 0, key=f"d{i}")

        st.session_state.rows[i] = row

    if st.button("他人データ保存"):

        now = datetime.datetime.now()

        headers = [
            "日時", "曜日", "機種", "ホール", "台番号",
            "回転", "前任者回転", "ぶどう", "チェリー",
            "BIG", "REG", "投資", "回収", "評価"
        ]

        sheet = connect_sheet("他人データ", headers)

        values = []

        for row in st.session_state.rows:
            values.append([
                now.strftime("%Y-%m-%d %H:%M"),
                now.strftime("%A"),
                row["機種"],
                SHOP_NAME,
                row["台番号"],
                row["回転"],
                0,
                0,
                0,
                row["BIG"],
                row["REG"],
                0,
                row["差枚"],
                ""
            ])

        if values:
            sheet.append_rows(values)

        st.success("保存完了")


# ==================================================
# ④ ホール分析AI
# ==================================================
with tab4:
    st.header("ホール分析AI")

    client = get_gspread_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    sheets = spreadsheet.worksheets()

    all_data = []

    for ws in sheets:
        name = ws.title

        if re.match(r"\d{4}-\d{2}-\d{2}", name):
            try:
                rows = ws.get_all_records()

                for row in rows:
                    row["日付"] = name
                    all_data.append(row)

            except:
                pass

    if all_data:

        df = pd.DataFrame(all_data)

        for col in ["REG確率", "合算", "台番"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["台番"])

        df["台番"] = df["台番"].astype(int)

        def score(row):
            try:
                if row["REG確率"] < 280 and row["合算"] < 120:
                    return 2
                elif row["REG確率"] < 330:
                    return 1
                else:
                    return -1
            except:
                return 0

        df["score"] = df.apply(score, axis=1)

        df["日付"] = pd.to_datetime(df["日付"])
        df["曜日"] = df["日付"].dt.day_name()

        # 曜日別
        st.subheader("曜日別")

        weekday_data = df.groupby("曜日")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=weekday_data.values,
            y=weekday_data.index,
            orientation="h"
        ))
        st.plotly_chart(fig, use_container_width=True)

        # 機種別
        st.subheader("機種別")

        machine_data = df.groupby("機種")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=machine_data.values,
            y=machine_data.index,
            orientation="h"
        ))
        st.plotly_chart(fig, use_container_width=True)

        # 末尾
        st.subheader("末尾")

        df["末尾"] = df["台番"] % 10

        sueo = df.groupby("末尾")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=sueo.values,
            y=sueo.index,
            orientation="h"
        ))
        st.plotly_chart(fig, use_container_width=True)

        # 並び
        st.subheader("並び（3台）")

        temp = df.sort_values("台番")
        temp["並び"] = temp["score"].rolling(3).mean()

        st.line_chart(temp["並び"])

        # ランキング
        st.subheader("おすすめ台ランキング")

        rank = df.groupby("台番")["score"].mean().sort_values(
            ascending=False
        )

        st.dataframe(rank.head(10))

    else:
        st.warning("DMMデータがまだありません")

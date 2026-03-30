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
# 機種リスト（全タブ共通）
# =============================
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
tab1, tab2, tab3, tab4 = st.tabs(["①DMMコピペ", "②個人カウント", "③複数台入力", "④ホール分析AI"])

# =============================
# ① DMMコピペ保存（本日〜6日前）
# =============================
with tab1:
    st.header("DMMデータ コピペ保存")

    st.write("【入力例】")
    st.code("""
本日
101 25 20 6500 1200
102 18 22 5800 -300

1日前
101 30 28 7200 2500
102 12 15 4000 -800
""")

    machine_name = st.selectbox("機種を選択", machine_list)
    paste_data = st.text_area("DMM表をコピーして貼り付け")

    if st.button("コピペデータ保存"):
        lines = paste_data.split("\n")
        today = datetime.date.today()
        target_date = today
        data_by_date = {}

        for line in lines:
            if "本日" in line:
                target_date = today
                continue
            elif "日前" in line:
                num = int(re.search(r'(\d+)日前', line).group(1))
                target_date = today - datetime.timedelta(days=num)
                continue

            nums = re.findall(r'-?\d+', line)
            if len(nums) >= 5:
                machine_no = nums[0]
                big = int(nums[1])
                reg = int(nums[2])
                spin = int(nums[3])
                diff = int(nums[4])

                gassan = spin / (big + reg) if (big + reg) > 0 else 0
                reg_prob = spin / reg if reg > 0 else 0

                date_str = target_date.strftime("%Y-%m-%d")

                if date_str not in data_by_date:
                    data_by_date[date_str] = []

                data_by_date[date_str].append([
                    machine_no, machine_name, spin, big, reg,
                    round(gassan,1), round(reg_prob,1), diff
                ])

        for date_str, data in data_by_date.items():
            df = pd.DataFrame(data, columns=[
                "台番","機種","回転数","BIG","REG","合算","REG確率","差枚"
            ])

            sheet = connect_sheet(date_str, df.columns.tolist())

            for _, row in df.iterrows():
                sheet.append_row(row.tolist())

        st.success("本日〜6日前まで日付ごとに保存しました")

# =============================
# ② 個人カウント（詳細版）
# =============================
with tab2:
    st.header("個人詳細データ")

    machine = st.selectbox("機種", machine_list)

    col1,col2,col3 = st.columns(3)

    with col1:
        machine_no = st.text_input("台番号")
        spin = st.number_input("現在回転",0)
        prev_spin = st.number_input("前任者回転",0)

    # チェリー
    st.header("🍒チェリー")
    cherry_free = st.number_input("フリー打ち", 0)
    cherry_aim = st.number_input("狙い打ち", 0)
    cherry = cherry_aim if cherry_aim > 0 else cherry_free

    # ボーナス内訳
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

    # 小役
    st.header("🍇小役")
    grape = st.number_input("ぶどう", 0)
    pierrot = st.number_input("ピエロ", 0)
    bell = st.number_input("ベル", 0)

    # 収支
    st.header("💰収支")
    invest = st.number_input("投資",0)
    collect = st.number_input("回収",0)

    total_spin = spin + prev_spin

    st.write("総回転:", total_spin)

    # 各確率
    if total_spin > 0:
        st.write("BIG確率:", round(total_spin / big_total,1) if big_total>0 else 0)
        st.write("REG確率:", round(total_spin / reg_total,1) if reg_total>0 else 0)
        st.write("合算:", round(total_spin / (big_total+reg_total),1) if (big_total+reg_total)>0 else 0)
        st.write("ぶどう確率:", round(total_spin / grape,2) if grape>0 else 0)
        st.write("単独REG率:", round(reg_single / reg_total,2) if reg_total>0 else 0)
        st.write("チェリーREG率:", round(reg_cherry / reg_total,2) if reg_total>0 else 0)

    if st.button("個人データ保存"):
        now = datetime.datetime.now()
        weekday = now.strftime("%A")
        eval_result = evaluate(total_spin,big_total,reg_total)

        headers = [
            "日時","曜日","機種","ホール","台番号",
            "回転","前任者回転","ぶどう","チェリー",
            "BIG","REG","投資","回収","評価"
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
            big_total,
            reg_total,
            invest,
            collect,
            eval_result
        ])
        st.success("保存完了")

# =============================
# ③ 複数台入力
# =============================
with tab3:
    st.header("複数台入力（他人データ）")

    if "rows" not in st.session_state:
        st.session_state.rows = []

    if st.button("台追加"):
        st.session_state.rows.append({})

    for i,row in enumerate(st.session_state.rows):
        c1,c2,c3,c4,c5,c6 = st.columns(6)

        row["機種"] = c1.selectbox("機種", machine_list, key=f"machine_{i}")
        row["台番号"] = c2.text_input("台番号", key=f"machine_no_{i}")
        row["回転"] = c3.number_input("回転", key=f"spin_{i}")
        row["BIG"] = c4.number_input("BIG", key=f"big_{i}")
        row["REG"] = c5.number_input("REG", key=f"reg_{i}")
        row["差枚"] = c6.number_input("差枚", key=f"diff_{i}")

    if st.button("他人データ保存"):
        now = datetime.datetime.now()

        headers = [
            "日時","曜日","機種","ホール","台番号",
            "回転","前任者回転","ぶどう","チェリー",
            "BIG","REG","投資","回収","評価"
        ]

        sheet = connect_sheet("他人データ", headers)

        for row in st.session_state.rows:
            sheet.append_row([
                now.strftime("%Y-%m-%d %H:%M"),
                now.strftime("%A"),
                row["機種"],
                SHOP_NAME,
                row["台番号"],
                row["回転"],
                0,0,0,
                row["BIG"],
                row["REG"],
                0,
                row["差枚"],
                ""
            ])
        st.success("保存完了")

# =============================
# ④ ホール分析AI
# =============================
with tab4:
    st.header("ホール分析AI（DMM分析）")

    client = get_gspread_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    sheets = spreadsheet.worksheets()

    all_data = []

    for sheet in sheets:
        name = sheet.title
        if re.match(r"\d{4}-\d{2}-\d{2}", name):
            data = sheet.get_all_records()
            for row in data:
                row["日付"] = name
                all_data.append(row)

    if len(all_data) > 0:
        df = pd.DataFrame(all_data)

        # 評価スコア
        def score(row):
            if row["REG確率"] < 280 and row["合算"] < 120:
                return 2
            elif row["REG確率"] < 330:
                return 1
            else:
                return -1

        df["score"] = df.apply(score, axis=1)
        df["台番"] = df["台番"].astype(int)

        # 日付→曜日
        df["日付"] = pd.to_datetime(df["日付"])
        df["曜日"] = df["日付"].dt.day_name()

        # -----------------
        # 曜日別（横グラフ）
        # -----------------
        st.subheader("曜日別")

        weekday_data = df.groupby("曜日")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=weekday_data.values,
            y=weekday_data.index,
            orientation='h'
        ))
        st.plotly_chart(fig, use_container_width=True)

        # -----------------
        # 機種別（横グラフ）
        # -----------------
        st.subheader("機種別")

        machine_data = df.groupby("機種")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=machine_data.values,
            y=machine_data.index,
            orientation='h'
        ))
        st.plotly_chart(fig, use_container_width=True)

        # -----------------
        # 末尾（横グラフ）
        # -----------------
        st.subheader("末尾")

        df["末尾"] = df["台番"] % 10
        sueo_data = df.groupby("末尾")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=sueo_data.values,
            y=sueo_data.index,
            orientation='h'
        ))
        st.plotly_chart(fig, use_container_width=True)

        # -----------------
        # 並び分析（3台並び）
        # -----------------
        st.subheader("並び（3台並び）")

        df_sorted = df.sort_values("台番")
        df_sorted["並びスコア"] = df_sorted["score"].rolling(3).mean()
        st.line_chart(df_sorted["並びスコア"])

        # -----------------
        # おすすめ台
        # -----------------
        st.subheader("おすすめ台ランキング")

        rank = df.groupby("台番")["score"].mean().sort_values(ascending=False)
        st.dataframe(rank.head(10))

    else:
        st.warning("DMMデータがまだありません")

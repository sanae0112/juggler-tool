import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re

st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO【上尾UNO】")

SHOP_NAME = "上尾UNO"
SPREADSHEET_NAME = "上尾UNO"

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
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="2000", cols="20")
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
# OCR 日付判定
# =============================
def get_date_from_text(text):
    today = datetime.date.today()

    if "本日" in text:
        return today.strftime("%Y-%m-%d")
    elif "1日前" in text:
        return (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif "2日前" in text:
        return (today - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    elif "3日前" in text:
        return (today - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    elif "4日前" in text:
        return (today - datetime.timedelta(days=4)).strftime("%Y-%m-%d")
    elif "5日前" in text:
        return (today - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
    else:
        return today.strftime("%Y-%m-%d")

# =============================
# タブ
# =============================
tab1, tab2, tab3, tab4 = st.tabs(["①DMM OCR/コピペ", "②個人カウント", "③複数台入力", "④AI分析"])

# =============================
# ① OCR + コピペ
# =============================
with tab1:
    st.header("DMMデータ OCR / コピペ保存")

    st.subheader("① OCR（スクショ読み取り）")
    uploaded_file = st.file_uploader("スクショ画像をアップ", type=["png","jpg","jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        img = np.array(image)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

        text = pytesseract.image_to_string(gray, lang="jpn+eng")

        st.text("OCR読み取り結果")
        st.text(text)

        sheet_date = get_date_from_text(text)
        st.write("保存先シート:", sheet_date)

        lines = text.split("\n")
        data = []

        for line in lines:
            nums = re.findall(r'-?\d+', line)
            if len(nums) >= 5:
                try:
                    machine_no = nums[0]
                    big = int(nums[1])
                    reg = int(nums[2])
                    spin = int(nums[3])
                    diff = int(nums[4])

                    gassan = spin / (big + reg) if (big + reg) > 0 else 0
                    reg_prob = spin / reg if reg > 0 else 0

                    data.append([
                        machine_no,"マイジャグラーV",spin,big,reg,
                        round(gassan,1),round(reg_prob,1),diff
                    ])
                except:
                    pass

        df = pd.DataFrame(data, columns=[
            "台番","機種","回転数","BIG","REG","合算","REG確率","差枚"
        ])

        st.dataframe(df)

        if st.button("OCRデータ保存"):
            sheet = connect_sheet(sheet_date, df.columns.tolist())
            for _, row in df.iterrows():
                sheet.append_row(row.tolist())
            st.success(f"{sheet_date} に保存しました")

    st.subheader("② コピペ保存")
    paste_data = st.text_area("DMM表をコピーして貼り付け")

    if st.button("コピペデータ保存"):
        lines = paste_data.split("\n")
        data = []

        for line in lines:
            nums = re.findall(r'-?\d+', line)
            if len(nums) >= 5:
                try:
                    machine_no = nums[0]
                    big = int(nums[1])
                    reg = int(nums[2])
                    spin = int(nums[3])
                    diff = int(nums[4])

                    gassan = spin / (big + reg) if (big + reg) > 0 else 0
                    reg_prob = spin / reg if reg > 0 else 0

                    data.append([
                        machine_no,"マイジャグラーV",spin,big,reg,
                        round(gassan,1),round(reg_prob,1),diff
                    ])
                except:
                    pass

        df = pd.DataFrame(data, columns=[
            "台番","機種","回転数","BIG","REG","合算","REG確率","差枚"
        ])

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        sheet = connect_sheet(today, df.columns.tolist())

        for _, row in df.iterrows():
            sheet.append_row(row.tolist())

        st.success("保存完了")
        st.dataframe(df)

# =============================
# ② 個人カウント
# =============================
with tab2:
    st.header("個人詳細データ")

    machine = st.selectbox("機種", [
        "マイジャグラーV","アイムジャグラーEX","ファンキージャグラー2",
        "ゴージャグラー3","ハッピージャグラーV3","ミスタージャグラー",
        "ジャグラーガールズ","ウルトラミラクルジャグラー"
    ])

    col1,col2,col3 = st.columns(3)

    with col1:
        machine_no = st.text_input("台番号")
        spin = st.number_input("現在回転",0)
        prev_spin = st.number_input("前任者回転",0)

    with col2:
        big = st.number_input("BIG",0)
        reg = st.number_input("REG",0)
        grape = st.number_input("ぶどう",0)
        cherry = st.number_input("チェリー",0)

    with col3:
        invest = st.number_input("投資",0)
        collect = st.number_input("回収",0)

    total_spin = spin + prev_spin
    st.write("総回転:", total_spin)

    if st.button("個人データ保存"):
        now = datetime.datetime.now()
        weekday = now.strftime("%A")
        eval_result = evaluate(total_spin,big,reg)

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
            big,
            reg,
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

        row["機種"] = c1.selectbox(
            "機種",
            [
                "マイジャグラーV","アイムジャグラーEX","ファンキージャグラー2",
                "ゴージャグラー3","ハッピージャグラーV3",
                "ミスタージャグラー","ジャグラーガールズ","ウルトラミラクルジャグラー"
            ],
            key=f"machine_{i}"
        )

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

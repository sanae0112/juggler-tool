import streamlit as st
import pandas as pd
import datetime
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go

st.set_page_config(page_title="Juggler Analyzer AI PRO", layout="wide")
st.title("🎰 Juggler Analyzer AI PRO【UNO】")

SHOP_NAME = "上尾UNO"
DMM_JACKPOT_URL = "https://p-town.dmm.com/shops/saitama/3602/jackpot"

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

def connect_sheet(sheet_name):
    client = get_gspread_client()
    spreadsheet = client.open("juggler_data")

    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="2000", cols="20")
        sheet.append_row([
            "日時","曜日","機種","ホール","台番号",
            "回転","前任者回転","ぶどう","チェリー",
            "BIG","REG","投資","回収","評価"
        ])
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
                    round(gassan,1), round(reg_prob,1), diff
                ])
            except:
                pass

    return pd.DataFrame(data, columns=[
        "台番","機種","回転数","BIG","REG","合算","REG確率","差枚"
    ])

# =============================
# 評価
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
tab1, tab2, tab3, tab4 = st.tabs(["①DMMデータ", "②個人カウント", "③複数台入力", "④AI分析"])

# =============================
# ① DMM
# =============================
with tab1:
    st.header("DMMデータ取得")

    if st.button("DMMデータ取得"):
        df = get_dmm_data()
        st.dataframe(df)

        st.subheader("差枚ランキング")
        st.dataframe(df.sort_values("差枚", ascending=False).head(10))

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

    if total_spin > 0 and reg > 0:
        reg_rate = total_spin / reg
        if reg_rate < 270:
            st.success("設定5以上期待")
        elif reg_rate < 300:
            st.warning("設定4以上")
        else:
            st.error("低設定")

    if st.button("個人データ保存"):
        now = datetime.datetime.now()
        weekday = now.strftime("%A")
        eval_result = evaluate(total_spin,big,reg)

        sheet = connect_sheet(machine+"_自分")

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
# ③ 複数台
# =============================
with tab3:
    st.header("複数台入力（他人データ）")

    if "rows" not in st.session_state:
        st.session_state.rows = []

    if st.button("台追加"):
        st.session_state.rows.append({})

    for i,row in enumerate(st.session_state.rows):
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        row["機種"] = c1.selectbox("機種",[
            "マイジャグラーV","アイムジャグラーEX","ファンキージャグラー2",
            "ゴージャグラー3","ハッピージャグラーV3",
            "ミスタージャグラー","ジャグラーガールズ","ウルトラミラクルジャグラー"
        ],key=i)
        row["台番号"] = c2.text_input("台番号",key=str(i))
        row["回転"] = c3.number_input("回転",key="s"+str(i))
        row["BIG"] = c4.number_input("BIG",key="b"+str(i))
        row["REG"] = c5.number_input("REG",key="r"+str(i))
        row["差枚"] = c6.number_input("差枚",key="d"+str(i))

    if st.button("他人データ保存"):
        now = datetime.datetime.now()
        for row in st.session_state.rows:
            sheet = connect_sheet(row["機種"]+"_他人")
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
# ④ AI分析（全機種）
# =============================
with tab4:
    st.header("おすすめ台AI（全機種）")

    machines = [
        "マイジャグラーV","アイムジャグラーEX","ファンキージャグラー2",
        "ゴージャグラー3","ハッピージャグラーV3",
        "ミスタージャグラー","ジャグラーガールズ","ウルトラミラクルジャグラー"
    ]

    if st.button("おすすめ台分析（全機種）"):
        all_data = pd.DataFrame()

        for machine in machines:
            try:
                sheet = connect_sheet(machine+"_自分")
                data = sheet.get_all_records()
                df = pd.DataFrame(data)
                all_data = pd.concat([all_data, df])
            except:
                pass

        if len(all_data) > 0:
            score_map = {"高":2,"中":1,"低":-1}
            all_data["score"] = all_data["評価"].map(score_map)

            result = all_data.groupby("台番号")["score"].mean()

            best = result.idxmax()
            st.success(f"🔥全機種おすすめ台：{best}")

            fig = go.Figure(go.Bar(
                x=result.values,
                y=result.index,
                orientation='h'
            ))
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("データがまだありません")

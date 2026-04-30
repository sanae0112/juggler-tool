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
# Google Sheets
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
    return gspread.authorize(credentials)

def connect_sheet(sheet_name, headers=None):
    client = get_gspread_client()
    spreadsheet = client.open(SPREADSHEET_NAME)

    for _ in range(3):
        try:
            return spreadsheet.worksheet(sheet_name)

        except WorksheetNotFound:
            ws = spreadsheet.add_worksheet(
                title=sheet_name,
                rows="5000",
                cols="30"
            )
            if headers:
                ws.append_row(headers)
            return ws

        except:
            time.sleep(1)

    st.error("Google Sheets接続失敗")
    st.stop()

# ==================================================
# 共通関数
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

def score_func(reg_prob, gassan):
    try:
        if reg_prob < 280 and gassan < 120:
            return 2
        elif reg_prob < 330:
            return 1
        else:
            return -1
    except:
        return 0

def color_rank(x):
    if x >= 1.5:
        return "🔴激アツ"
    elif x >= 1.0:
        return "🟠強い"
    elif x >= 0.3:
        return "🟡普通"
    else:
        return "⚪弱い"

# ==================================================
# タブ
# ==================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "①DMMコピペ",
    "②個人カウント",
    "③複数台入力",
    "④ホール分析AI",
    "⑤並びAI PRO"
])

# ==================================================
# ① DMMコピペ保存
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
                    if num <= 10:
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

                    total = big + reg
                    gassan = round(spin / total, 1) if total else 0
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

            ws = connect_sheet(date_str, headers)
            ws.append_rows(rows)

        st.success("保存完了")

# ==================================================
# ② 個人カウント
# ==================================================
with tab2:
    st.header("個人詳細データ")

    machine = st.selectbox("機種", machine_list, key="solo")

    machine_no = st.text_input("台番号")
    spin = st.number_input("現在回転", 0)
    prev_spin = st.number_input("前任者回転", 0)

    grape = st.number_input("ぶどう", 0)
    cherry = st.number_input("チェリー", 0)

    big = st.number_input("BIG", 0)
    reg = st.number_input("REG", 0)

    invest = st.number_input("投資", 0)
    collect = st.number_input("回収", 0)

    total_spin = spin + prev_spin

    if st.button("個人データ保存"):

        ws = connect_sheet(
            "個人データ",
            [
                "日時","曜日","機種","ホール","台番号",
                "回転","前任者回転","ぶどう","チェリー",
                "BIG","REG","投資","回収","評価"
            ]
        )

        now = datetime.datetime.now()

        ws.append_row([
            now.strftime("%Y-%m-%d %H:%M"),
            now.strftime("%A"),
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
            evaluate(total_spin, big, reg)
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
        c1,c2,c3,c4,c5,c6 = st.columns(6)

        row = {}
        row["機種"] = c1.selectbox("機種", machine_list, key=f"m{i}")
        row["台番号"] = c2.text_input("台番号", key=f"n{i}")
        row["回転"] = c3.number_input("回転", 0, key=f"s{i}")
        row["BIG"] = c4.number_input("BIG", 0, key=f"b{i}")
        row["REG"] = c5.number_input("REG", 0, key=f"r{i}")
        row["差枚"] = c6.number_input("差枚", 0, key=f"d{i}")

        st.session_state.rows[i] = row

    if st.button("他人データ保存"):

        ws = connect_sheet(
            "他人データ",
            [
                "日時","曜日","機種","ホール","台番号",
                "回転","前任者回転","ぶどう","チェリー",
                "BIG","REG","投資","回収","評価"
            ]
        )

        now = datetime.datetime.now()
        values = []

        for row in st.session_state.rows:
            values.append([
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

        ws.append_rows(values)
        st.success("保存完了")

# ==================================================
# 共通：DMM読み込み
# ==================================================
def load_dmm():
    client = get_gspread_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    sheets = spreadsheet.worksheets()

    rows = []

    for ws in sheets:
        if re.match(r"\d{4}-\d{2}-\d{2}", ws.title):
            try:
                data = ws.get_all_records()

                for r in data:
                    r["日付"] = ws.title
                    rows.append(r)

            except:
                pass

    if len(rows) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    for c in ["台番","REG確率","合算"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["台番"])
    df["台番"] = df["台番"].astype(int)
    df["score"] = df.apply(
        lambda x: score_func(x["REG確率"], x["合算"]),
        axis=1
    )

    return df

# ==================================================
# ④ ホール分析AI
# ==================================================
with tab4:
    st.header("ホール分析AI")

    df = load_dmm()

    if len(df) == 0:
        st.warning("DMMデータなし")
    else:
        df["日付"] = pd.to_datetime(df["日付"])
        df["曜日"] = df["日付"].dt.day_name()

        st.subheader("曜日別")
        wk = df.groupby("曜日")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=wk.values,
            y=wk.index,
            orientation="h"
        ))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("機種別")
        mc = df.groupby("機種")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=mc.values,
            y=mc.index,
            orientation="h"
        ))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("末尾")
        df["末尾"] = df["台番"] % 10
        su = df.groupby("末尾")["score"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=su.values,
            y=su.index,
            orientation="h"
        ))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("おすすめ台")
        rank = df.groupby("台番")["score"].mean().sort_values(
            ascending=False
        )
        st.dataframe(rank.head(10))

# ==================================================
# ⑤ 並びAI PRO
# ==================================================
with tab5:
    st.header("並びAI PRO【上尾UNO専用】")

    df = load_dmm()

    if len(df) == 0:
        st.warning("DMMデータなし")
        st.stop()

    machine_map = {
        "ネオアイムジャグラー":
            list(range(640,648)) +
            list(range(662,670)) +
            list(range(728,735)),

        "マイジャグラーV":
            list(range(648,662)),

        "ミスタージャグラー":
            list(range(685,688)),

        "ウルトラミラクルジャグラー":
            list(range(688,692)),

        "ジャグラーガールズ":
            list(range(692,699)),

        "ファンキージャグラー2":
            list(range(699,709)),

        "ハッピージャグラーV3":
            list(range(721,728))
    }

    def make_rank(data, span=3):
        tmp = data.groupby("台番")["score"].mean().reset_index()
        score_map = dict(zip(tmp["台番"], tmp["score"]))
        nums = sorted(score_map.keys())

        rows = []

        for i in range(len(nums)-span+1):
            g = nums[i:i+span]

            if g[-1] - g[0] == span-1:
                avg = round(
                    sum(score_map[n] for n in g) / span, 2
                )

                rows.append([
                    f"{g[0]}-{g[-1]}",
                    avg,
                    color_rank(avg)
                ])

        if len(rows) == 0:
            return pd.DataFrame(
                columns=["台番範囲","平均スコア","評価"]
            )

        r = pd.DataFrame(
            rows,
            columns=["台番範囲","平均スコア","評価"]
        )

        return r.sort_values(
            "平均スコア",
            ascending=False
        ).head(10)

    # ---------------------------
    # 機種内3台
    # ---------------------------
    st.subheader("機種内3台 TOP10")

    box = []

    for mc, nums in machine_map.items():
        temp = df[df["台番"].isin(nums)]
        r = make_rank(temp, 3)

        if len(r):
            r["機種"] = mc
            box.append(r)

    final3 = pd.concat(box).sort_values(
        "平均スコア",
        ascending=False
    ).head(10)

    st.dataframe(final3)

    # ---------------------------
    # 跨ぎ3台
    # ---------------------------
    st.subheader("跨ぎ3台 TOP10")
    cross3 = make_rank(df, 3)
    st.dataframe(cross3)

    # ---------------------------
    # 機種内2台
    # ---------------------------
    st.subheader("機種内2台 TOP10")

    box2 = []

    for mc, nums in machine_map.items():
        temp = df[df["台番"].isin(nums)]
        r = make_rank(temp, 2)

        if len(r):
            r["機種"] = mc
            box2.append(r)

    final2 = pd.concat(box2).sort_values(
        "平均スコア",
        ascending=False
    ).head(10)

    st.dataframe(final2)

    # ---------------------------
    # 跨ぎ2台
    # ---------------------------
    st.subheader("跨ぎ2台 TOP10")
    cross2 = make_rank(df, 2)
    st.dataframe(cross2)

    # ---------------------------
    # シート保存（1シート集約）
    # ---------------------------
    if st.button("ランキング保存"):

        ws = connect_sheet(
            "並びAIランキング",
            [
                "保存日",
                "種類",
                "順位",
                "台番範囲",
                "機種",
                "平均スコア",
                "評価"
            ]
        )

        today = datetime.date.today().strftime("%Y-%m-%d")
        values = []

        def push_rows(name, data):
            for i, row in data.reset_index(drop=True).iterrows():

                machine = row["機種"] if "機種" in row else "混合"

                values.append([
                    today,
                    name,
                    i+1,
                    row["台番範囲"],
                    machine,
                    row["平均スコア"],
                    row["評価"]
                ])

        push_rows("機種内3台", final3)
        push_rows("跨ぎ3台", cross3)
        push_rows("機種内2台", final2)
        push_rows("跨ぎ2台", cross2)

        ws.append_rows(values)

        st.success("ランキング保存完了")

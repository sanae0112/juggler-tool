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
# がりぞう実戦値
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

# チェリー
st.header("🍒チェリー")
cherry_free = st.number_input("フリー打ち", 0)
cherry_aim = st.number_input("狙い打ち", 0)
cherry = cherry_aim if cherry_aim > 0 else cherry_free

# ボーナス
st.header("🎰ボーナス")
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

# ======================
# 複数台UI（機種選択付き）
# ======================
st.header("📥追加：複数台入力（UI＋機種選択）")

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

    # ★修正ポイント
    big_p = row["回転"]/row["BIG"] if row["BIG"] > 0 else None
    reg_p = row["回転"]/row["REG"] if row["REG"] > 0 else None

    def fmt(v): return f"{v:,.1f}" if v else "-"
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

    st.markdown(f"""
    BIG確率: <span style='color:{col(big_p)}'>{fmt(big_p)}</span>
    REG確率: <span style='color:{col(reg_p)}'>{fmt(reg_p)}</span>
    """, unsafe_allow_html=True)

# ======================
# 複数台保存（機種別）
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
        # ======================
# 🧠 設定推測AI（横棒グラフ＋％表示）
# ======================
st.header("🧠 設定推測AI（確率表示）")

if total_spin > 0:

    spec = garizo_specs[machine]
    weights = spec["weights"]
    data = spec["data"]

    scores = {}

    for setting in range(1,7):
        s = data[setting]
        score = 0

        # ===== REG =====
        if "reg" in s and reg_total > 0:
            reg_rate = total_spin / reg_total
            score += weights.get("reg",0) * abs(reg_rate - s["reg"])

        # ===== ぶどう =====
        if "grape" in s and grape > 0:
            grape_rate = total_spin / grape
            score += weights.get("grape",0) * abs(grape_rate - s["grape"])

        # ===== チェリーREG =====
        if "cherry_reg" in s and reg_total > 0:
            cherry_reg_rate = reg_cherry / reg_total
            score += weights.get("cherry_reg",0) * abs(cherry_reg_rate - s["cherry_reg"])

        # ===== ミスター系 =====
        if "pierrot" in s and pierrot > 0:
            score += weights.get("pierrot",0) * abs((total_spin / pierrot) - s["pierrot"])

        if "bell" in s and bell > 0:
            score += weights.get("bell",0) * abs((total_spin / bell) - s["bell"])

        if "cherry_big" in s and big_total > 0:
            score += weights.get("cherry_big",0) * abs((big_cherry / big_total) - s["cherry_big"])

        if "pierrot_big" in s and big_total > 0:
            score += weights.get("pierrot_big",0) * abs((big_pierrot / big_total) - s["pierrot_big"])

        if "pierrot_reg" in s and reg_total > 0:
            score += weights.get("pierrot_reg",0) * abs((reg_pierrot / reg_total) - s["pierrot_reg"])

        scores[setting] = score

    # ======================
    # スコア → 確率変換
    # ======================
    max_score = max(scores.values())
    min_score = min(scores.values())

    probs = {}

    for k,v in scores.items():
        if max_score - min_score == 0:
            probs[k] = 100/6
        else:
            probs[k] = (max_score - v)

    total = sum(probs.values())
    for k in probs:
        probs[k] = round((probs[k] / total) * 100, 1)

    # ======================
    # 推定表示
    # ======================
    best = max(probs, key=probs.get)
    st.subheader(f"🎯 推定設定：設定{best}（{probs[best]}%）")

    # ======================
    # 横棒グラフ
    # ======================
    df = pd.DataFrame({
        "設定": [f"設定{k}" for k in probs.keys()],
        "確率": list(probs.values())
    })

    df = df.sort_values("確率", ascending=True)

    fig = go.Figure(go.Bar(
        x=df["確率"],
        y=df["設定"],
        orientation='h'
    ))

    fig.update_layout(
        xaxis_title="信頼度（%）",
        yaxis_title="設定",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # ======================
    # 詳細
    # ======================
    with st.expander("詳細（確率）"):
        st.write(probs)

else:
    st.info("回転数を入力するとAI推測が動きます")
    # ======================
# 🎯 打つ / ヤメ判定AI
# ======================
st.header("🎯 打つ・ヤメ判定")

decision = "様子見"

if total_spin > 0 and reg_total > 0:

    reg_rate = total_spin / reg_total
    total_bonus = big_total + reg_total
    combined = total_spin / total_bonus if total_bonus > 0 else 999

    best_prob = probs[best] if 'probs' in locals() else 0

    if best_prob > 60 and reg_rate < 300:
        decision = "🟢 継続推奨（高設定期待）"
    elif best_prob > 40:
        decision = "🟡 様子見"
    else:
        decision = "🔴 ヤメ推奨"

    st.subheader(decision)

# ======================
# 💾 保存時に評価付与
# ======================
def evaluate_row(spin, big, reg):
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
# 💾 保存処理（評価付き）
# ======================
def save_with_eval(row, mode):
    now = datetime.datetime.now()

    weekday = now.strftime("%A")  # 曜日

    eval_result = evaluate_row(row["回転"], row["BIG"], row["REG"])

    sheet = connect_sheet_mode(row["機種"], mode)

    sheet.append_row([
        now.strftime("%Y-%m-%d %H:%M"),
        weekday,
        row["機種"],
        shop,
        row["台番号"],
        row["回転"],
        0,0,0,
        row["BIG"],
        row["REG"],
        0,
        row["差枚"],
        eval_result
    ])

# ======================
# 🧠 おすすめ台AI
# ======================
st.header("🧠 おすすめ台AI")

if st.button("おすすめ台を分析"):
    sheet = connect_sheet_mode(machine, "自分")
    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    if len(df) > 0:
        result = df.groupby("台番号")["投資"].count()

        # 評価集計
        eval_counts = df.groupby(["台番号","回収"]).size().unstack(fill_value=0)

        scores = {}

        for idx in eval_counts.index:
            high = eval_counts.loc[idx].get("高",0)
            mid = eval_counts.loc[idx].get("中",0)
            low = eval_counts.loc[idx].get("低",0)

            total = high + mid + low
            if total == 0:
                continue

            score = (high*2 + mid*1 - low*1) / total
            scores[idx] = score

        if scores:
            best_machine = max(scores, key=scores.get)
            st.success(f"🔥おすすめ台：{best_machine}")

            st.write(scores)
# ======================
# 🧠 総合おすすめAI（曜日×ホール×台）
# ======================
st.header("🧠 総合おすすめAI（曜日×ホール×台）")

if st.button("最強おすすめ分析"):

    sheet = connect_sheet_mode(machine, "自分")
    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    if len(df) == 0:
        st.warning("データがありません")
    else:

        # ===== 評価数値化 =====
        def score_map(x):
            if x == "高": return 2
            if x == "中": return 1
            if x == "低": return -1
            return 0

        df["score"] = df["評価"].map(score_map)

        # ===== 台別 =====
        machine_score = df.groupby("台番号")["score"].mean()

        # ===== 曜日別 =====
        weekday_score = df.groupby("曜日")["score"].mean()

        # ===== ホール別 =====
        hall_score = df.groupby("ホール")["score"].mean()

        # ===== 総合スコア =====
        total_scores = {}

        for _, row in df.iterrows():
            m = row["台番号"]
            w = row["曜日"]
            h = row["ホール"]

            score = (
                machine_score.get(m,0)*0.5 +
                weekday_score.get(w,0)*0.3 +
                hall_score.get(h,0)*0.2
            )

            total_scores[m] = score

        # ===== 最強台 =====
        if total_scores:
            best = max(total_scores, key=total_scores.get)

            st.success(f"🔥最強おすすめ台：{best}")

            # 可視化
            df_score = pd.DataFrame({
                "台番号": list(total_scores.keys()),
                "スコア": list(total_scores.values())
            }).sort_values("スコア")

            fig = go.Figure(go.Bar(
                x=df_score["スコア"],
                y=df_score["台番号"],
                orientation='h'
            ))

            st.plotly_chart(fig, use_container_width=True)

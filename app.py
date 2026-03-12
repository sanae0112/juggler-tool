import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. データベース (現行全機種フルデータ) ---
juggler_db = {
    "マイジャグラーV": {
        "big_s": [390.1, 385.5, 372.4, 352.3, 334.4, 321.3],
        "big_c": [1213.6, 1191.6, 1170.3, 1129.9, 1074.4, 1024.0],
        "reg_s": [630.2, 595.8, 504.1, 420.1, 385.5, 321.3],
        "reg_c": [1213.6, 1170.3, 1092.3, 1024.0, 936.2, 840.2],
        "grape": [5.90, 5.86, 5.82, 5.78, 5.74, 5.66],
        "cherry": [36.0, 35.8, 35.5, 35.1, 34.8, 34.0],
        "wari": [97.0, 98.0, 99.9, 102.8, 105.3, 109.4]
    },
    "アイムジャグラーEX": {
        "big_s": [409.6, 404.5, 404.5, 385.5, 385.5, 376.6],
        "big_c": [819.2, 819.2, 819.2, 780.2, 780.2, 799.2],
        "reg_s": [630.2, 595.8, 468.1, 439.8, 337.8, 337.8],
        "reg_c": [1213.6, 1213.6, 1092.3, 1092.3, 1024.0, 1024.0],
        "grape": [6.02, 6.02, 6.02, 6.02, 6.02, 5.78],
        "cherry": [35.5, 35.1, 34.8, 34.1, 33.7, 33.0],
        "wari": [97.0, 98.0, 99.5, 101.1, 103.3, 105.5]
    },
    "ファンキージャグラー2": {
        "big_s": [372.4, 364.1, 341.3, 318.1, 292.6, 268.6],
        "big_c": [936.2, 936.2, 910.2, 862.3, 819.2, 744.7],
        "reg_s": [642.5, 606.8, 555.4, 496.5, 442.8, 409.6],
        "reg_c": [1310.7, 1213.6, 1170.3, 1057.0, 936.2, 862.3],
        "grape": [6.10, 6.08, 6.04, 6.00, 5.95, 5.85],
        "cherry": [36.5, 36.3, 36.0, 35.7, 35.3, 34.5],
        "wari": [97.0, 98.5, 100.2, 102.0, 104.3, 109.0]
    },
    "ゴーゴージャグラー3": {
        "big_s": [372.4, 368.2, 364.1, 344.9, 318.1, 297.9],
        "big_c": [963.8, 936.2, 910.2, 862.3, 819.2, 744.7],
        "reg_s": [528.5, 481.9, 442.8, 394.8, 352.3, 321.3],
        "reg_c": [1129.9, 1057.0, 993.0, 910.2, 840.2, 744.7],
        "grape": [5.95, 5.92, 5.89, 5.86, 5.83, 5.76],
        "cherry": [36.0, 35.8, 35.5, 35.2, 34.9, 34.2],
        "wari": [97.0, 98.2, 99.4, 101.6, 103.5, 106.0]
    },
    "ハッピージャグラーVIII": {
        "big_s": [409.6, 399.6, 390.1, 372.4, 348.6, 334.4],
        "big_c": [1092.3, 1057.0, 1024.0, 963.8, 910.2, 862.3],
        "reg_s": [606.8, 565.0, 496.5, 431.2, 390.1, 352.3],
        "reg_c": [1310.7, 1213.6, 1092.3, 1024.0, 936.2, 862.3],
        "grape": [5.95, 5.91, 5.87, 5.83, 5.79, 5.70],
        "cherry": [36.0, 35.8, 35.5, 35.2, 34.9, 34.5],
        "wari": [97.0, 98.1, 99.9, 102.9, 105.8, 108.4]
    },
    "ミスタージャグラー": {
        "big_s": [409.6, 404.5, 394.8, 381.0, 364.1, 352.3],
        "big_c": [1024.0, 1008.2, 978.1, 936.2, 885.6, 840.2],
        "reg_s": [630.2, 585.1, 516.1, 442.8, 390.1, 352.3],
        "reg_c": [1213.6, 1170.3, 1092.3, 1024.0, 936.2, 840.2],
        "grape": [5.98, 5.94, 5.90, 5.86, 5.82, 5.72],
        "cherry": [35.6, 35.4, 35.1, 34.8, 34.6, 34.1],
        "wari": [97.0, 98.2, 100.2, 102.5, 104.9, 107.3]
    },
    "ジャグラーガールズSS": {
        "big_s": [390.1, 381.0, 372.4, 348.6, 327.7, 312.1],
        "big_c": [910.2, 885.6, 862.3, 819.2, 780.2, 712.3],
        "reg_s": [585.1, 546.1, 481.9, 414.8, 381.0, 341.3],
        "reg_c": [1260.3, 1170.3, 1092.3, 993.0, 910.2, 819.2],
        "grape": [6.00, 5.97, 5.94, 5.90, 5.85, 5.75],
        "cherry": [35.8, 35.5, 35.2, 34.9, 34.5, 33.8],
        "wari": [97.0, 98.2, 100.1, 103.3, 105.8, 107.5]
    }
}

# --- 2. 画面設定 & デザイン ---
st.set_page_config(page_title="Ultimate Juggler Tool", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1a1c24; border-radius: 10px; padding: 15px; border-left: 5px solid #ff00ff; }
    .stButton>button { border-radius: 20px; background: linear-gradient(45deg, #722f91, #ff00ff); color: white; border: none; width: 100%; height: 3em; font-weight: bold; }
    h1, h2, h3 { color: #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. セッション管理 (収支保存用) ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["日付", "ホール", "機種", "投資", "回収", "収支", "回転数", "推定設定"])

# --- 4. サイドバーメニュー ---
st.sidebar.title("🎰 JUG MENU")
menu = st.sidebar.radio("機能を選択", ["設定推測 & 逆算", "シマ配分分析", "収支アナリティクス", "周辺店舗検索"])
model_name = st.sidebar.selectbox("対象機種を選択", list(juggler_db.keys()))

# --- 5. メイン機能：設定推測 & 逆算 ---
if menu == "設定推測 & 逆算":
    st.title("🎯 ピンポイント設定判別")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 前任者データ")
        pre_g = st.number_input("前任 回転数", value=1000, step=100)
        pre_b = st.number_input("前任 BIG", value=3)
        pre_r = st.number_input("前任 REG", value=2)
        
    with col2:
        st.subheader("🙋 自分データ")
        my_g = st.number_input("自分 回転数", value=500, step=100)
        my_samai = st.number_input("自分の区間の差枚数", value=0)
        my_b_s = st.number_input("自分 単独BIG", value=0)
        my_b_c = st.number_input("自分 チェリーBIG", value=0)
        my_r_s = st.number_input("自分 単独REG", value=0)
        my_r_c = st.number_input("自分 チェリーREG", value=0)

    # 逆算ぶどうロジック
    my_b_total = my_b_s + my_b_c
    my_r_total = my_r_s + my_r_c
    # 払い出し計算 (BIG240, REG96, 他小役0.3枚/Gと仮定)
    my_grape_count = max(1, int(((my_g * 3) + my_samai - (my_b_total*240 + my_r_total*96) - (my_g*0.3)) / 8))
    
    st.divider()
    st.metric("🍇 あなたの区間の逆算ぶどう", f"1/{round(my_g/my_grape_count, 2)}")

    if st.button("全データで設定推測を実行"):
        data = juggler_db[model_name]
        log_probs = np.zeros(6)
        total_g = pre_g + my_g
        total_b = pre_b + my_b_total
        total_r = pre_r + my_r_total
        
        for i in range(6):
            # ボーナス(合算近似) + 自分の逆算ぶどう
            p_b = 1/((data["big_s"][i]+data["big_c"][i])/2)
            p_r = 1/((data["reg_s"][i]+data["reg_c"][i])/2)
            p_g = 1/data["grape"][i]
            
            # 対数尤度計算
            score = total_b * np.log(p_b) + (total_g - total_b) * np.log(1-p_b)
            score += total_r * np.log(p_r) + (total_g - total_r) * np.log(1-p_r)
            score += my_grape_count * np.log(p_g) + (my_g - my_grape_count) * np.log(1-p_g)
            log_probs[i] = score
            
        probs = (np.exp(log_probs - np.max(log_probs)) / np.exp(log_probs - np.max(log_probs)).sum()) * 100
        
        # 結果表示
        res_col1, res_col2 = st.columns([1, 1])
        with res_col1:
            fig = go.Figure(data=[go.Pie(labels=[f"設定{i+1}" for i in range(6)], values=probs, hole=.4, marker=dict(colors=px.colors.sequential.RdBu))])
            fig.update_layout(template="plotly_dark", title="設定期待度比率", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with res_col2:
            top_s = np.argmax(probs) + 1
            st.subheader(f"推測結果: 設定 {top_s}")
            st.write(f"期待時給: 約 {int((data['wari'][top_s-1]/100 - 1) * 800 * 3 * 20)} 円")
            # やめどきアドバイス
            if top_s >= 4: st.success("🔥 続行推奨！高設定の可能性が高いです。")
            else: st.error("⚠️ 撤退検討。低設定の数値です。")

# --- 6. シマ配分分析 ---
elif menu == "シマ配分分析":
    st.title("🔍 シマ合算・配分推測")
    total_shima_g = st.number_input("シマ全体の総回転数", value=10000, step=1000)
    total_shima_b = st.number_input("シマ全体の総BIG", value=40)
    total_shima_r = st.number_input("シマ全体の総REG", value=30)
    
    if st.button("シマ配分を分析"):
        avg_合算 = total_shima_g / (total_shima_b + total_shima_r)
        st.metric("シマ平均合算", f"1/{round(avg_合算, 1)}")
        if avg_合算 < 135: st.success("このシマには高設定が複数投入されている可能性があります！")
        else: st.warning("シマ全体の配分は低めです。ピンポイント狙いが必要です。")

# --- 7. 収支アナリティクス ---
elif menu == "収支アナリティクス":
    st.title("📊 収支ダッシュボード")
    with st.expander("実戦結果を入力"):
        h_name = st.text_input("ホール名")
        toushi = st.number_input("投資(枚)", value=500, step=50)
        kaishu = st.number_input("回収(枚)", value=1000, step=10)
        if st.button("データを追加"):
            new_data = pd.DataFrame([[datetime.now().date(), h_name, model_name, toushi, kaishu, kaishu-toushi, 0, "未設定"]], columns=st.session_state.history.columns)
            st.session_state.history = pd.concat([st.session_state.history, new_data], ignore_index=True)
            st.success("追加しました")

    if not st.session_state.history.empty:
        st.dataframe(st.session_state.history)
        fig_bal = px.line(st.session_state.history, x=st.session_state.history.index, y=st.session_state.history["収支"].cumsum(), title="累計収支推移")
        st.plotly_chart(fig_bal)

# --- 8. 周辺店舗検索 ---
elif menu == "周辺店舗検索":
    st.title("🌐 周辺店舗データ検索")
    shop_q = st.text_input("ホール名を入力してください")
    if shop_q:
        st.write(f"🔗 [アナスロで {shop_q} を検索](https://anaslo.com{shop_q})")
        st.write(f"🔗 [みんレポで {shop_q} を検索](https://min-repo.com{shop_q})")

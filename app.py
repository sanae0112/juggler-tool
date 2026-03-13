import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 全機種データベース (6号機ジャグラー全網羅) ---
juggler_db = {
    "マイジャグラーV": {"big_s": [390.1, 385.5, 372.4, 352.3, 334.4, 321.3], "big_c": [1213.6, 1191.6, 1170.3, 1129.9, 1074.4, 1024.0], "reg_s": [630.2, 595.8, 504.1, 420.1, 385.5, 321.3], "reg_c": [1213.6, 1170.3, 1092.3, 1024.0, 936.2, 840.2], "grape": [5.90, 5.86, 5.82, 5.78, 5.74, 5.66], "wari": [97.0, 98.0, 99.9, 102.8, 105.3, 109.4]},
    "アイムジャグラーEX": {"big_s": [409.6, 404.5, 404.5, 385.5, 385.5, 376.6], "big_c": [819.2, 819.2, 819.2, 780.2, 780.2, 799.2], "reg_s": [630.2, 595.8, 468.1, 439.8, 337.8, 337.8], "reg_c": [1213.6, 1213.6, 1092.3, 1092.3, 1024.0, 1024.0], "grape": [6.02, 6.02, 6.02, 6.02, 6.02, 5.78], "wari": [97.0, 98.0, 99.5, 101.1, 103.3, 105.5]},
    "ファンキージャグラー2": {"big_s": [372.4, 364.1, 341.3, 318.1, 292.6, 268.6], "big_c": [936.2, 936.2, 910.2, 862.3, 819.2, 744.7], "reg_s": [642.5, 606.8, 555.4, 496.5, 442.8, 409.6], "reg_c": [1310.7, 1213.6, 1170.3, 1057.0, 936.2, 862.3], "grape": [6.10, 6.08, 6.04, 6.00, 5.95, 5.85], "wari": [97.0, 98.5, 100.2, 102.0, 104.3, 109.0]},
    "ゴーゴージャグラー3": {"big_s": [372.4, 368.2, 364.1, 344.9, 318.1, 297.9], "big_c": [963.8, 936.2, 910.2, 862.3, 819.2, 744.7], "reg_s": [528.5, 481.9, 442.8, 394.8, 352.3, 321.3], "reg_c": [1129.9, 1057.0, 993.0, 910.2, 840.2, 744.7], "grape": [5.95, 5.92, 5.89, 5.86, 5.83, 5.76], "wari": [97.0, 98.2, 99.4, 101.6, 103.5, 106.0]},
    "ハッピージャグラーVIII": {"big_s": [409.6, 399.6, 390.1, 372.4, 348.6, 334.4], "big_c": [1092.3, 1057.0, 1024.0, 963.8, 910.2, 862.3], "reg_s": [606.8, 565.0, 496.5, 431.2, 390.1, 352.3], "reg_c": [1310.7, 1213.6, 1092.3, 1024.0, 936.2, 862.3], "grape": [5.95, 5.91, 5.87, 5.83, 5.79, 5.70], "wari": [97.0, 98.1, 99.9, 102.9, 105.8, 108.4]},
    "ミスタージャグラー": {"big_s": [409.6, 404.5, 394.8, 381.0, 364.1, 352.3], "big_c": [1024.0, 1008.2, 978.1, 936.2, 885.6, 840.2], "reg_s": [630.2, 585.1, 516.1, 442.8, 390.1, 352.3], "reg_c": [1213.6, 1170.3, 1092.3, 1024.0, 936.2, 840.2], "grape": [5.98, 5.94, 5.90, 5.86, 5.82, 5.72], "wari": [97.0, 98.2, 100.2, 102.5, 104.9, 107.3]},
    "ジャグラーガールズSS": {"big_s": [390.1, 381.0, 372.4, 348.6, 327.7, 312.1], "big_c": [910.2, 885.6, 862.3, 819.2, 780.2, 712.3], "reg_s": [585.1, 546.1, 481.9, 414.8, 381.0, 341.3], "reg_c": [1260.3, 1170.3, 1092.3, 993.0, 910.2, 819.2], "grape": [6.00, 5.97, 5.94, 5.90, 5.85, 5.75], "wari": [97.0, 98.2, 100.1, 103.3, 105.8, 107.5]}
}

# --- 2. 画面設定 & 接続 ---
st.set_page_config(page_title="Ultimate Juggler Analyzer", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1a1c24; border-radius: 10px; padding: 15px; border-left: 5px solid #ff00ff; }
    .stButton>button { border-radius: 20px; background: linear-gradient(45deg, #722f91, #ff00ff); color: white; width: 100%; height: 3em; font-weight: bold; border: none; }
    h1, h2, h3 { color: #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. サイドバーメニュー ---
st.sidebar.title("🎰 MENU")
menu = st.sidebar.radio("モード切替", ["設定推測 & 逆算", "収支管理・クラウド保存", "周辺店舗検索"])
model_name = st.sidebar.selectbox("機種選択", list(juggler_db.keys()))

# --- 4. メイン機能：設定推測 & 逆算 ---
if menu == "設定推測 & 逆算":
    st.title("🎯 究極設定判別")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 前任者")
        pre_g = st.number_input("回転数", value=1000, step=100)
        pre_b = st.number_input("BIG", value=3)
        pre_r = st.number_input("REG", value=2)
    with col2:
        st.subheader("🙋 自分")
        my_g = st.number_input("回転数", value=500, step=100)
        my_samai = st.number_input("区間差枚数", value=200)
        my_b_s = st.number_input("単独BIG", value=2)
        my_b_c = st.number_input("重複BIG", value=0)
        my_r_s = st.number_input("単独REG", value=1)
        my_r_c = st.number_input("重複REG", value=0)

    # 逆算ぶどう計算
    my_b_total = my_b_s + my_b_c
    my_r_total = my_r_s + my_r_c
    my_grape = max(1, int(((my_g * 3) + my_samai - (my_b_total*240 + my_r_total*96) - (my_g*0.3)) / 8))
    
    st.divider()
    st.metric("🍇 あなたの区間の逆算ぶどう", f"1/{round(my_g/my_grape, 2)}")

    if st.button("全データで設定推測を実行"):
        data = juggler_db[model_name]
        log_probs = np.zeros(6)
        total_g = pre_g + my_g
        total_b = pre_b + my_b_total
        total_r = pre_r + my_r_total
        
        for i in range(6):
            p_b = 1/((data["big_s"][i]+data["big_c"][i])/2)
            p_r = 1/((data["reg_s"][i]+data["reg_c"][i])/2)
            p_g = 1/data["grape"][i]
            score = total_b * np.log(p_b) + (total_g - total_b) * np.log(1-p_b)
            score += total_r * np.log(p_r) + (total_g - total_r) * np.log(1-p_r)
            score += my_grape * np.log(p_g) + (my_g - my_grape) * np.log(1-p_g)
            log_probs[i] = score
            
        probs = (np.exp(log_probs - np.max(log_probs)) / np.exp(log_probs - np.max(log_probs)).sum()) * 100
        fig = go.Figure(data=[go.Pie(labels=[f"設定{i+1}" for i in range(6)], values=probs, hole=.4)])
        fig.update_layout(template="plotly_dark", title="設定期待度")
        st.plotly_chart(fig)
        
        best_s = np.argmax(probs) + 1
        st.info(f"💰 推定期待時給: 約 {int((data['wari'][best_s-1]/100 - 1) * 800 * 3 * 20)} 円")

# --- 5. 収支管理 & 保存 ---
elif menu == "収支管理・クラウド保存":
    st.title("📊 収支管理 & 保存")
    with st.form("save_form"):
        hall = st.text_input("ホール名", value="A店")
        toushi = st.number_input("投資(枚)", value=500, step=50)
        kaishu = st.number_input("回収(枚)", value=1000, step=10)
        memo = st.selectbox("最終的な推定設定", [1, 2, 3, 4, 5, 6], index=3)
        submit = st.form_submit_button("クラウドに保存")
        
        if submit:
            try:
                df = conn.read()
                new_data = pd.DataFrame([{"日付": datetime.now().strftime("%Y-%m-%d"), "ホール": hall, "機種": model_name, "投資": toushi, "回収": kaishu, "収支": kaishu-toushi, "回転数": 0, "推定設定": memo}])
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(data=updated_df)
                st.balloons()
                st.success("スプレッドシートに保存完了！")
            except Exception as e:
                st.error(f"エラー: {e}")

# --- 6. 周辺店舗検索 ---
elif menu == "周辺店舗検索":
    st.title("🔍 周辺データ検索")
    shop = st.text_input("ホール名を入力")
    if shop:
        st.write(f"🔗 [アナスロで {shop} を検索](https://anaslo.com{shop})")
        st.write(f"🔗 [みんレポで {shop} を検索](https://min-repo.com{shop})")

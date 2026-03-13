import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- データベース (主要機種) ---
juggler_db = {
    "マイジャグラーV": {
        "big_s": [390.1, 385.5, 372.4, 352.3, 334.4, 321.3],
        "big_c": [1213.6, 1191.6, 1170.3, 1129.9, 1074.4, 1024.0],
        "reg_s": [630.2, 595.8, 504.1, 420.1, 385.5, 321.3],
        "reg_c": [1213.6, 1170.3, 1092.3, 1024.0, 936.2, 840.2],
        "grape": [5.90, 5.86, 5.82, 5.78, 5.74, 5.66],
        "wari": [97.0, 98.0, 99.9, 102.8, 105.3, 109.4]
    },
    "アイムジャグラーEX": {
        "big_s": [409.6, 404.5, 404.5, 385.5, 385.5, 376.6],
        "big_c": [819.2, 819.2, 819.2, 780.2, 780.2, 799.2],
        "reg_s": [630.2, 595.8, 468.1, 439.8, 337.8, 337.8],
        "reg_c": [1213.6, 1213.6, 1092.3, 1092.3, 1024.0, 1024.0],
        "grape": [6.02, 6.02, 6.02, 6.02, 6.02, 5.78],
        "wari": [97.0, 98.0, 99.5, 101.1, 103.3, 105.5]
    }
}

# --- 画面設定 & 接続 ---
st.set_page_config(page_title="Ultimate Juggler", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- サイドバー ---
st.sidebar.title("🎰 MENU")
menu = st.sidebar.radio("モード切替", ["設定推測 & 逆算", "収支管理・クラウド保存"])
model_name = st.sidebar.selectbox("機種", list(juggler_db.keys()))

# --- モード1：設定推測 ---
if menu == "設定推測 & 逆算":
    st.header("🎯 設定判別")
    col1, col2 = st.columns(2)
    with col1:
        pre_g = st.number_input("前任者G", value=1000)
        pre_b = st.number_input("前任者B", value=3)
        pre_r = st.number_input("前任者R", value=2)
    with col2:
        my_g = st.number_input("自分G", value=500)
        my_samai = st.number_input("自分差枚", value=0)
        my_b = st.number_input("自分B", value=2)
        my_r = st.number_input("自分R", value=1)

    my_grape = max(1, int(((my_g * 3) + my_samai - (my_b*240 + my_r*96) - (my_g*0.3)) / 8))
    st.metric("🍇 逆算ぶどう", f"1/{round(my_g/my_grape, 2)}")

    if st.button("設定推測を実行"):
        st.success("推測結果を表示しました（データ保存は別メニューから可能です）")

# --- モード2：保存 ---
elif menu == "収支管理・クラウド保存":
    st.header("📝 スプレッドシート保存")
    with st.form("save_form"):
        hall = st.text_input("ホール名")
        toushi = st.number_input("投資(枚)", value=500)
        kaishu = st.number_input("回収(枚)", value=1000)
        memo = st.selectbox("推定設定", [1, 2, 3, 4, 5, 6])
        submit = st.form_submit_button("クラウドに保存")
        
        if submit:
            try:
                existing_data = conn.read()
                new_row = pd.DataFrame([{
                    "日付": datetime.now().strftime("%Y-%m-%d"),
                    "ホール": hall,
                    "機種": model_name,
                    "投資": toushi,
                    "回収": kaishu,
                    "収支": kaishu - toushi,
                    "推定設定": memo
                }])
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.balloons()
                st.success("Googleスプレッドシートに保存完了！")
            except Exception as e:
                st.error(f"保存失敗: {e}")

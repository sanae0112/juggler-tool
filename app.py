import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="Juggler Analyzer", layout="wide")
st.title("🎰 Juggler Analyzer")

# ======================
# Google Sheets 接続（Secrets版）
# ======================

def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open("juggler_data").sheet1
    return sheet

# ======================
# 機種
# ======================

machine = st.selectbox("機種", [
    "アイムジャグラーEX",
    "マイジャグラーV",
    "ファンキージャグラー2",
    "ゴーゴージャグラー3",
    "ハッピージャグラーV3",
    "ミスタージャグラー",
    "ジャグラーガールズSS",
    "ウルトラミラクルジャグラー"
])

# ======================
# ホール
# ======================

st.header("🏠ホール")

shop = st.text_input("ホール名")
machine_no = st.text_input("台番号")

if shop == "":
    st.warning("ホール名を入力してください")
    st.stop()

# ======================
# 回転数
# ======================

st.header("🎯回転数")

spin = st.number_input("現在回転", 0)
prev_spin = st.number_input("前任者回転", 0)

total_spin = spin + prev_spin
st.write("総回転:", total_spin)

# ======================
# 小役
# ======================

st.header("🍒小役")

grape = st.number_input("🍇ぶどう", 0)
cherry = st.number_input("🍒チェリー", 0)
middle_cherry = st.number_input("中段チェリー", 0)

# ======================
# BIG（ビック）
# ======================

st.header("🔴ビック")

big_single = st.number_input("単独ビック", 0)
big_cherry = st.number_input("チェリービック", 0)
big_pierrot = st.number_input("ピエロビック", 0)
big_one = st.number_input("一枚役ビック", 0)

# ======================
# REG（バケ）
# ======================

st.header("🔵バケ")

reg_single = st.number_input("単独バケ", 0)
reg_cherry = st.number_input("チェリーバケ", 0)
reg_pierrot = st.number_input("ピエロバケ", 0)
reg_one = st.number_input("一枚役バケ", 0)

# ======================
# 合計
# ======================

big_total = big_single + big_cherry + big_pierrot + big_one
reg_total = reg_single + reg_cherry + reg_pierrot + reg_one

# ======================
# 確率
# ======================

st.header("📊確率")

if total_spin > 0:

    total_bonus = big_total + reg_total

    if total_bonus > 0:
        st.write("合算 1/", round(total_spin / total_bonus, 1))

    if big_total > 0:
        st.write("ビック 1/", round(total_spin / big_total, 1))

    if reg_total > 0:
        st.write("バケ 1/", round(total_spin / reg_total, 1))

    if grape > 0:
        st.write("ぶどう 1/", round(total_spin / grape, 1))

    if cherry > 0:
        st.write("チェリー 1/", round(total_spin / cherry, 1))

# ======================
# チェリー重複率
# ======================

st.header("🍒チェリー重複率")

cherry_bonus = big_cherry + reg_cherry

if cherry > 0:
    rate = cherry_bonus / cherry * 100
    st.write("チェリー重複率:", round(rate, 2), "%")

# ======================
# 収支
# ======================

st.header("💰収支")

investment = st.number_input("投資", 0)
recovery = st.number_input("回収", 0)

profit = recovery - investment
st.write("差枚:", profit)

# ======================
# 保存
# ======================

if st.button("保存"):

    sheet = connect_sheet()

    now = datetime.datetime.now()

    sheet.append_row([
        now.strftime("%Y-%m-%d %H:%M"),
        machine,
        shop,
        machine_no,
        spin,
        prev_spin,
        grape,
        cherry,
        middle_cherry,
        big_single,
        big_cherry,
        big_pierrot,
        big_one,
        reg_single,
        reg_cherry,
        reg_pierrot,
        reg_one,
        investment,
        recovery
    ])

    st.success("保存しました")

# ======================
# 履歴分析
# ======================

st.header("📈履歴分析")

if st.button("履歴読み込み"):

    sheet = connect_sheet()
    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    if len(df) > 0:

        df["差枚"] = df["回収"] - df["投資"]

        st.dataframe(df)

        st.write("総収支:", df["差枚"].sum())
        st.write("勝率:", round(len(df[df["差枚"] > 0]) / len(df) * 100, 1), "%")

        # 日別
        df["日付"] = df["日時"].str[:10]
        st.write("日別収支")
        st.bar_chart(df.groupby("日付")["差枚"].sum())

        # 月別
        df["月"] = df["日時"].str[:7]
        st.write("月別収支")
        st.bar_chart(df.groupby("月")["差枚"].sum())

        # 店別
        st.write("店別収支")
        st.bar_chart(df.groupby("ホール")["差枚"].sum())

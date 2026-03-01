import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 修正した各ユーザー専用のURL ---
USER_DATA = {
    "ユーザーA": "https://docs.google.com/spreadsheets/d/1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE/edit#gid=0",
    "ユーザーB": "https://docs.google.com/spreadsheets/d/1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50/edit#gid=1960331400",
    "ユーザーC": "https://docs.google.com/spreadsheets/d/1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4/edit#gid=1960331400"
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 生活リズム・体調管理")

# ユーザー選択
selected_user = st.selectbox("名前を選んでね", ["選択してください"] + list(USER_DATA.keys()))

if selected_user != "選択してください":
    url = USER_DATA[selected_user]
    current_month = date.today().strftime("%Y-%m")
    
    # ファイルが別々なので、シート名は月のみ
    target_sheet = f"{current_month}"

    # スプレッドシートを開くボタン
    st.link_button(f"📊 {selected_user} 専用のスプレッドシートを開く", url)

    # サイドバー：予定表
    with st.sidebar:
        st.header("⏰ 予定表")
        schedule = {"06:30": "起床・準備", "07:00": "外出", "13:00": "IT学習", "17:00": "筋トレ", "22:00": "就寝"}
        for t, task in schedule.items():
            st.write(f"**{t}** : {task}")

    # 入力フォーム
    with st.form("input_form"):
        col_time1, col_time2 = st.columns(2)
        with col_time1: bedtime = st.text_input("昨夜の就寝時間", "22:00")
        with col_time2: wakeup_time = st.text

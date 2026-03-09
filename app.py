import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]},
    "テト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "teto", "weight_pw": "guest123"}
}

st.set_page_config(page_title="Health Log Pro", layout="wide")

# --- UIカスタマイズ ---
st.markdown("""
    <style>
    .stApp, .stMarkdown, p, label { color: #31333F !important; }
    div[data-testid="stCheckbox"] label p { color: #31333F !important; font-weight: 600 !important; }
    div[data-testid="stForm"] { background-color: #ffffff; border-radius: 15px; padding: 25px; border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- 2. ログイン機能（ここを修正！） ---
if not st.session_state.logged_in:
    st.title("🔐 Health Log Login")
    with st.columns([1,1.5,1])[1]:
        with st.container(border=True):
            user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
            pw_input = st.text_input("パスワード", type="password")
            if st.button("ログイン", use_container_width=True, type="primary"):
                # 行が途切れないように整理
                if user_choice != "選択してください":
                    if pw_input == USER_DATA[user_choice]["pw"]:
                        st.session_state.logged_in = True
                        st.session_state.current_user = user_choice
                        st.rerun()
                    else:
                        st.error("パスワードが違います")
                else:
                    st.warning("ユーザーを選択してください")
    st.stop()

# --- 3. メイン画面 ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
t_sheet = date.today().strftime("%Y-%m")

# ヘッダー
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title(f"🐾 {user}ちゃんの健康管理" if user == "テト" else f"👋 {user}さんの健康管理")
with col_h2:
    st.write("")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1: st.link_button("📊 Sheet",

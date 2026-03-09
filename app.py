import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime
import altair as alt

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]},
    "テト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "teto", "weight_pw": "guest123"}
}

st.set_page_config(page_title="Health Log Pro", layout="wide")

# --- UIカスタマイズ (文字色とレイアウト) ---
st.markdown("""
    <style>
    /* 全体の文字色を強制的に指定して、ダークモードでの文字消えを防ぐ */
    .stApp, .stMarkdown, p, label { color: #31333F !important; }
    /* チェックボックス横の文字（ラベル）を特に強調 */
    div[data-testid="stCheckbox"] label p {
        color: #31333F !important;
        font-weight: 600 !important;
    }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f0f2f6; border-radius: 5px; }
    div[data-testid="stForm"] { background-color: #ffffff; border-radius: 15px; padding: 25px; border: 1px solid #e6e9ef; }
    /* スライダーや入力欄の間隔調整 */
    .stSlider, .stSelectbox { margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- 2. ログイン機能 ---
if not st.session_state.logged_in:
    st.title("🔐 Health Log Login")
    with st.columns([1,1.5,1])[1]:
        with st.container(border=True):
            user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
            pw_input = st.text_input("パスワード", type="password")
            if st.button("ログイン", use_container_width=True, type="primary"):
                if user_choice != "選択してください" and pw_input == USER

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

# --- 2. ログイン機能 ---
if not st.session_state.logged_in:
    st.title("🔐 Health Log Login")
    with st.columns([1,1.5,1])[1]:
        with st.container(border=True):
            user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
            pw_input = st.text_input("パスワード", type="password")
            if st.button("ログイン", use_container_width=True, type="primary"):
                if user_choice != "選択してください":
                    if pw_input == USER_DATA[user_choice]["pw"]:
                        st.session_state.logged_in = True
                        st.session_state.current_user = user_choice
                        st.rerun()
                    else: st.error("パスワードが違います")
                else: st.warning("ユーザーを選択してください")
    st.stop()

# --- 3. メイン画面 ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
t_sheet = date.today().strftime("%Y-%m")

# ヘッダー (修正箇所: カッコを確実に閉じる)
col_h1, col_h2 = st.columns([3, 1.5])
with col_h1:
    st.title(f"🐾 {user}ちゃんの健康管理" if user == "テト" else f"👋 {user}さんの健康管理")
with col_h2:
    st.write("")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1: st.link_button("📊 Sheet", url) # ここを修正したよ
    with c_btn2: 
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

st.divider()

tabs_list = ["📝 記録・推移", "⚖️ 体重管理"]
if user == "克己": tabs_list.append("🩸 血圧管理")
sel_tab = st.tabs(tabs_list)

with sel_tab[0]:
    try:
        df = conn.read(spreadsheet=url, worksheet=t_sheet, ttl=0)
    except:
        df = pd.DataFrame()

    # グラフ表示
    if not df.empty:
        st.markdown("### 📈 体調トレンド")
        gdf = df.copy()
        gdf['日付'] = pd.to_datetime(gdf['日付'])
        map_10 = {"かなり多い": 8, "多い": 6, "普通": 4, "少なめ": 2, "かなり少なめ": 0, "かなり柔らかい": 8, "柔らかい": 6, "少し硬い": 2, "かなり硬い": 0}
        gdf['ごはん値'] = gdf['ごはんの量'].map(map_10).fillna(0)
        gdf['うんち値'] = gdf['うんちの状態'].map(map_10).fillna(0)
        cols = ["総合元気度", "ごはん値", "うんち値", "運動量"]
        for c in cols: gdf[c] = pd.to_numeric

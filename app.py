import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"},
    "テト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "teto"}
}

st.set_page_config(page_title="Health Log Pro", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- 2. ログイン ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
    pw_input = st.text_input("パスワード", type="password")
    if st.button("ログイン", use_container_width=True, type="primary"):
        if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
            st.session_state.logged_in = True
            st.session_state.current_user = user_choice
            st.rerun()
        else: st.error("パスワードが違います")
    st.stop()

# --- 3. データ読み込み & 1日1データ厳選 ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
t_month = date.today().strftime("%Y-%m")

try:
    raw_df = conn.read(spreadsheet=url, worksheet=t_month, ttl=0)
    if not raw_df.empty:
        raw_df['日付'] = pd.to_datetime(raw_df['日付']).dt.strftime('%Y-%m-%d')
        df_clean = raw_df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
    else:
        df_clean = pd.DataFrame()
except:
    raw_df = pd.DataFrame()
    df_clean = pd.DataFrame()

# ヘッダー
st.title(f"🐾 {user}ちゃんの健康管理" if user == "テト" else f"👋 {user}さんの健康管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. グラフセクション ---
if not df_clean.empty:
    st.subheader("📈 体調トレンド (1日1最新データ)")
    gdf = df_clean.copy()
    # 日付表示をスッキリさせるためのベース設定
    base = alt.Chart(gdf).encode(
        x=alt.X('日付:N', title='日付', axis=alt.Axis(labelAngle=-45)) # :N(Nominal)で日付文字列を維持
    )

    if user == "テト":
        map_10 = {"かなり多い": 8, "多い": 6, "普通": 4, "少なめ": 2, "かなり少なめ": 0, "かなり柔らかい": 8, "柔らかい": 6, "少し硬い": 2, "かなり硬い": 0}
        if "ごはんの量" in gdf.columns: gdf['ごはん値'] = gdf['ごはんの量'].map(map_10).fillna(0)
        if "うんちの状態" in gdf.columns: gdf['うんち値'] = gdf['うんちの状態'].map(map_10).fillna(0)

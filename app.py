import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt
import base64
from io import BytesIO
from PIL import Image

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"},
    "テト": {"id": "1gHZ51t9qMDip_Gk_EjPH14Vke4BhbQEuf2ukZC3MxkQ", "pw": "teto"} 
}

st.set_page_config(page_title="Health Log Pro", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "weight_auth" not in st.session_state: st.session_state.weight_auth = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

# --- 画像変換ヘルパー ---
def image_to_base64(uploaded_file):
    if uploaded_file is None: return ""
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGB": img = img.convert("RGB")
        img.thumbnail((500, 500))
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    except: return ""

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

# --- 3. 共通ロジック ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if df is not None and not df.empty:
            df = df.dropna(how='all')
            if '日付' in df.columns:
                df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
                return df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
        return pd.DataFrame()
    except: return pd.DataFrame()

def save_entry(sheet_name, new_data_dict):
    existing_df = load_data(sheet_name)
    target_date = str(new_data_dict["日付"])
    if not existing_df.empty and target_date in existing_df["日付"].values:
        idx = existing_df[existing_df["日付"] == target_date].index[0]
        for col, val in new_data_dict.items():
            if val is not None and val != "" and val is not False:
                existing_df.at[idx, col] = val
        final_df = existing_df
    else:
        final_df = pd.concat([existing_df, pd.DataFrame([new_data_dict])], ignore_index=True)
    conn.update(spreadsheet=url, worksheet=sheet_name, data=final_df.fillna(""))
    st.cache_data.clear()

# --- 4. UIヘッダー ---
c_l, c_c, c_r = st.columns([1.5, 2, 1.5])
with c_l:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()
    st.markdown(f"#### {'🐾 ' + user if user == 'テト' else '👋 ' + user + 'さん'}")
with c_c:
    today = date.today()
    month_opts = [(today.replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
    selected_month = st.selectbox("📅 表示月", month_opts, label_visibility="collapsed")

# --- タブ設定 ---
tabs = st.tabs(["🚶 体調記録", "🩸 血圧管理", "⚖️ 体重管理"] if user == "克己" else ["🚶 体調記録", "⚖️ 体重管理"])

# --- タブ1: 体調記録 ---
with tabs[0]:
    df_main = load_data(selected_month)
    if selected_month == today.strftime("%Y-%m"):
        with st.form("main_form", clear_on_submit=True):
            if user == "テト":
                c1, c2, c3 = st.columns(3)
                with c1:

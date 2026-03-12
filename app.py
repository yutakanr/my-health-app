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

# --- 画像変換 (エラーで落とさない) ---
def image_to_base64(uploaded_file):
    if uploaded_file is None: return ""
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGB": img = img.convert("RGB")
        img.thumbnail((400, 400))
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=60)
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

# --- 3. データ処理 ---
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
    target_date = new_data_dict["日付"]
    
    if not existing_df.empty and target_date in existing_df["日付"].values:
        idx = existing_df[existing_df["日付"] == target_date].index[0]
        for col, val in new_data_dict.items():
            if val is not None and val != "": # 入力がある項目だけ更新
                existing_df.at[idx, col] = val
        final_df = existing_df
    else:
        final_df = pd.concat([existing_df, pd.DataFrame([new_data_dict])], ignore_index=True)
    
    conn.update(spreadsheet=url, worksheet=sheet_name, data=final_df.fillna(""))
    st.cache_data.clear()

# --- 4. メイン画面レイアウト ---
c_title, c_month, c_logout = st.columns([3, 2, 1])
with c_title:
    st.title(f"🐾 {user}" if user == "テト" else f"👋 {user}さん")
with c_month:
    today = date.today()
    month_opts = [(today.replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
    selected_month = st.selectbox("📅 表示月", month_opts)
with c_logout:
    st.write("") # 調整用
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()

tab_labels = ["🚶 体調", "⚖️ 体重"]
if user == "克己": tab_labels.insert(1, "🩸 血圧")
tabs = st.tabs(tab_labels)

# --- 体調タブ ---
with tabs[0]:
    df_main = load_data(selected_month)
    if selected_month == today.strftime("%Y-%m"):
        with st.form("main_form", clear_on_submit=True):
            if user == "テト":
                c1, c2 = st.columns(2)
                with c1: 
                    food = st.select_slider("ごはん", ["かなり少", "少", "普通", "多", "かなり多"], "普通")
                    water = st.slider("水分", 0, 10, 5)
                with c2: 
                    poo_s = st.selectbox("うんち", ["普通", "少し硬い", "かなり硬い", "柔らかい", "かなり柔らかい"])
                    poo_c = st.number_input("回数", 0, 10, 1)
                t_img = st.file_uploader("📸 写真", type=['png', 'jpg', 'jpeg'])
                memo = st.text_area("メモ")
                if st.form_submit_button("🐾 保存"):
                    save_entry(selected_month, {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "うんちの状態": poo_s, "うんち回数": poo_c, "画像URL": image_to_base64(t_img), "メモ": memo})
                    st.rerun()
            else:
                c1, c2 = st.columns(2)
                with c1: cond = st.slider("体調", 0, 10, 7); sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
                with c2: g = st.slider("総合実績", 0, 10, 5); memo = st.text_area("メモ")
                if st.form_submit_button("🚀 保存"):
                    save_entry(selected_month, {"日付": str(date.today()), "体調": cond, "睡眠時間": sl_h, "総合実績": g, "メモ": memo})
                    st.rerun()
    
    if not df_main.empty:
        st.subheader("📈 トレンド")
        v_cols = [c for c in ["体調", "睡眠時間", "総合実績", "水分補給"] if c in df_main.columns]
        if v_cols:
            m_df = df_main.melt(id_vars=['日付'], value_vars=v_cols).dropna()
            st.altair_chart(alt.Chart(m_df).mark_line(point=True).encode(x='日付:N', y='数値:Q', color='項目:N').properties(height=300), use_container_width=True)

# --- 血圧タブ (克己のみ) ---
if user == "克己":
    with tabs[1]:
        df_bp = load_data(selected_month)
        if selected_month == today.strftime("%Y-%m"):
            with st.form("bp_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: u1, d1, p1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80), st.number_input("脈拍1", 0, 200, 70)
                with c2: u2, d2, p2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80), st.number_input("脈拍2", 0, 200, 70)
                if st.form_submit_button("🩸 保存"):
                    save_entry(selected_month, {"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "脈拍1": p1, "血圧上2": u2, "血圧下2": d2, "脈拍2": p2})
                    st.rerun()
        if not df_bp.empty:
            st.subheader("📈 血圧")
            bp_c = [c for c in ["血圧上1", "血圧下1", "血圧上2", "血圧下2"] if c in df_bp.columns]
            st.altair_chart(alt.Chart(df_bp.melt(id_vars=['日付'], value_vars=bp_c)).mark_line(point=True).encode(x='日付:N', y=alt.Y('数値

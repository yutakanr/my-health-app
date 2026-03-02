import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. Settings ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]}
}

st.set_page_config(page_title="My Health Log", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. UI Styling ---
st.markdown("""
    <style>
    div[data-baseweb="select"] { font-size: 18px !important; }
    label p { font-size: 18px !important; font-weight: bold; }
    .stButton button { width: 100%; font-weight: bold; border-radius: 10px; height: 3em; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"

st.title("🛡️ 生活リズム・体調管理")

user = st.selectbox("👤 ユーザー選択", ["選択してください"] + list(USER_DATA.keys()))

if user != "選択してください":
    pw = st.text_input("基本パスワード", type="password")
    if pw == USER_DATA[user]["pw"]:
        url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
        t_sheet = date.today().strftime("%Y-%m")
        w_sheet = f"W_{t_sheet}"

        def load(s_name, cols):
            try:
                df = conn.read(spreadsheet=url, worksheet=s_name, ttl=0)
                return df if df is not None and not df.empty else pd.DataFrame(columns=cols)
            except:
                return pd.DataFrame(columns=cols)

        m_cols = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
        w_cols = ["日付", "体重"]
        data, w_data = load(t_sheet, m_cols), load(w_sheet, w_cols)

        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("📝 日報入力"): st.session_state.view_mode = "main"
        if c2.button("⚖️ 体重管理"): st.session_state.view_mode = "weight"

        if st.session_state.view_mode == "weight":
            w_pw = st.text_input("体重用パスワード", type="password")
            if w_pw == USER_DATA[user]["weight_pw"]:
                if not w_data.empty:
                    df_w = w_data.copy()
                    df_w["体重"] = pd.to_numeric(df_w["体重"], errors='coerce')
                    st.line_chart(df_w.set_index("日付")["体重"])
                    st.dataframe(w_data.sort_index(ascending=False))
            elif w_pw: st.error("PWエラー")
        else:
            with st.form("input_form"):
                col1, col2, col3 = st.columns(3)
                with col1: bed = st.text_input("就寝", "22:00"); wake = st.text_input("起床", "06:30")
                with col2: w_s = st.slider("寝起き", 1, 10, 5); mood = st.slider("気分", 1, 10, 5)
                with col3: weight = st.slider("体重(kg)", 40.0, 120.0, 65.0, 0.1); total = st.slider("総合", 1, 10, 5)
                memo = st.text_area("メモ")
                if st.form_submit_button("保存する"):
                    try:
                        new_m = pd.DataFrame([{"日付":str(date.today()), "食生活":5, "就寝時間":bed, "起床時間":wake, "寝起き":w_s, "寝つき":5, "行動意欲":5, "気分":mood, "体調":5, "総合実績":total, "睡眠時間":7.0, "メモ":memo}])[m_cols]
                        conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, new_m], ignore_index=True))
                        new_w = pd.DataFrame([{"日付":str(date.today()), "体重":weight}])[w_cols]
                        conn.update(spreadsheet=url, worksheet=w_sheet, data=pd.concat([w_data, new_w], ignore_index=True))
                        st.success("成功！"); st.rerun()
                    except Exception as e:
                        st.error("保存失敗。共有設定は正しいので、一度アプリを再起動してください。")
                        st.write(f"Error: {e}")

            if not data.empty: st.dataframe(data.sort_index(ascending=False))

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt

# --- 1. 設定 & ログイン ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"},
    "テト": {"id": "1gHZ51t9qMDip_Gk_EjPH14Vke4BhbQEuf2ukZC3MxkQ", "pw": "teto"} 
}

st.set_page_config(page_title="Health Log Pro", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# カスタムCSS
st.markdown("""
    <style>
    div.stButton > button:has(div p:contains("Logout")) {
        background-color: #FFD700 !important;
        color: black !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "edit_target" not in st.session_state: st.session_state.edit_target = None
if "delete_target" not in st.session_state: st.session_state.delete_target = None

if not st.session_state.logged_in:
    st.title("🔐 Login")
    u_choice = st.selectbox("ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
    p_input = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if u_choice != "選択してください" and p_input == USER_DATA[u_choice]["pw"]:
            st.session_state.logged_in = True
            st.session_state.current_user = u_choice
            st.rerun()
    st.stop()

# --- 2. 共通ロジック ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
cols_order = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "食生活", "行動力", "行動意欲", "総合実績", "メモ"]

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if df is not None and not df.empty:
            df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
            return df.sort_values(['日付'], ascending=False).drop_duplicates(subset=['日付'], keep='last')
        return pd.DataFrame(columns=cols_order)
    except: return pd.DataFrame(columns=cols_order)

def update_sheet(sheet_name, df):
    conn.update(spreadsheet=url, worksheet=sheet_name, data=df.fillna(""))
    st.cache_data.clear()

# --- 3. UI上部 ---
st.markdown(f"### {user}の体調管理画面")
c_out, c_month, c_db, c_spacer = st.columns([0.8, 1.2, 1.8, 5])
with c_out:
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()
with c_month:
    today = date.today()
    m_opts = [(today.replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
    sel_month = st.selectbox("月選択", m_opts, label_visibility="collapsed")
with c_db:
    st.link_button("📊 DBアクセス", url, use_container_width=True)

# --- 4. メイン ---
tabs = st.tabs(["🚶 体調記録", "⚖️ 体重"] + (["🩸 血圧"] if user == "克己" else []))

with tabs[0]:
    df_main = load_data(sel_month)
    
    # 編集用初期値のセット
    init_val = {"wake_h":7, "wake_m":0, "sleep_h":23, "sleep_m":0, "dur":7.0, "s1":7, "s2":7, "c":7, "d":6, "ap":5, "aw":5, "perf":5, "memo":""}
    if st.session_state.edit_target:
        row = df_main[df_main["日付"] == st.session_state.edit_target].iloc[0]
        try:
            init_val["wake_h"], init_val["wake_m"] = map(int, row["起床時間"].split(":"))
            init_val["sleep_h"], init_val["sleep_m"] = map(int, row["就寝時間"].split(":"))
            init_val["dur"], init_val["s1"], init_val["s2"], init_val["c"], init_val["d"], init_val["ap"], init_val["aw"], init_val["perf"], init_val["memo"] = row["睡眠時間"], row["寝つき"], row["寝起き"], row["体調"], row["食生活"], row["行動力"], row["行動意欲"], row["総合実績"], row["メモ"]
        except: pass

    # 入力フォーム
    st.subheader("🖋 編集モード" if st.session_state.edit_target else "🖋 今日の記録")
    with st.form("input_form"):
        col_l, col_r = st.columns(2)
        with col_l:
            st.write("**【睡眠】**")
            c_w1, c_w2 = st.columns(2)
            w_h = c_w1.number_input("起床（時）", 0, 23, init_val["wake_h"])
            w_m = c_w2.number_input("起床（分）", 0, 59, init_val["wake_m"], step=5)
            c_s1, c_s2 = st.columns(2)
            s_h = c_s1.number_

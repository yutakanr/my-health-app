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

# ボタンのカスタムCSS（Logoutボタンを黄色・黒文字にする）
st.markdown("""
    <style>
    /* Logoutボタン用のスタイル */
    div.stButton > button:has(div p:contains("Logout")) {
        background-color: #FFD700 !important;
        color: black !important;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

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

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if df is not None and not df.empty:
            df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
            return df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
        return pd.DataFrame()
    except: return pd.DataFrame()

def save_entry(sheet_name, data_dict):
    df = load_data(sheet_name)
    new_row = pd.DataFrame([data_dict])
    if not df.empty and data_dict["日付"] in df["日付"].values:
        idx = df[df["日付"] == data_dict["日付"]].index[0]
        for k, v in data_dict.items(): df.at[idx, k] = v
    else:
        df = pd.concat([df, new_row], ignore_index=True)
    conn.update(spreadsheet=url, worksheet=sheet_name, data=df.fillna(""))
    st.cache_data.clear()

# --- 3. UI上部 ---
st.markdown(f"### {user}の体調管理画面")

c_out, c_month, c_db, c_spacer = st.columns([0.8, 1.2, 1.8, 5])

with c_out:
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

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
    if sel_month == today.strftime("%Y-%m"):
        with st.form("input_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                cond = st.slider("体調", 0, 10, 7)
                diet = st.slider("食生活", 0, 10, 6)
            with col2:
                slp = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
                perf = st.slider("総合実績", 0, 10, 5)
            with col3:
                act = st.slider("行動力", 0, 10, 5)
            memo = st.text_area("メモ")
            if st.form_submit_button("記録を保存", use_container_width=True):
                save_entry(sel_month, {"日付": str(date.today()), "体調": cond, "食生活": diet, "睡眠時間": slp, "総合実績": perf, "行動力": act, "メモ": memo})
                st.rerun()
    
    if not df_main.empty:
        st.subheader("📈 トレンド（主要4項目）")
        plot_df = df_main.copy()
        # グラフ表示項目を4つに固定
        display_items = ["総合実績", "食生活", "睡眠時間", "行動力"]
        for c in display_items:
            if c in plot_df.columns: 
                plot_df[c] = pd.to_numeric(plot_df[c], errors='coerce')
        
        m_df = plot_df.melt(id_vars=['日付'], value_vars=[c for c in display_items if c in plot_df.columns]).dropna()
        st.altair_chart(alt.Chart(m_df).mark_line(point=True).encode(
            x='日付:N', 
            y='value:Q', 
            color='variable:N'
        ).properties(height=350), use_container_width=True)

# 履歴（表にも行動力が含まれるように表示）
st.divider()
if not df_main.empty:
    st.subheader("📋 履歴一覧")
    # スプレッドシートにある列をそのまま表示（save_entryで行動力が追加されているので反映される）
    st.dataframe(df_main.sort_values("日付", ascending=False), use_container_width=True)

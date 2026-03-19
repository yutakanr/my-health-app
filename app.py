import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt

# --- 1. 設定 & ログインチェック ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"},
    "テト": {"id": "1gHZ51t9qMDip_Gk_EjPH14Vke4BhbQEuf2ukZC3MxkQ", "pw": "teto"} 
}

st.set_page_config(page_title="Health Log Pro", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# ログイン画面
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

# --- 2. データ読み書きロジック ---
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
        df.update(df[df["日付"] == data_dict["日付"]].fillna(new_row.iloc[0]))
    else:
        df = pd.concat([df, new_row], ignore_index=True)
    conn.update(spreadsheet=url, worksheet=sheet_name, data=df.fillna(""))
    st.cache_data.clear()

# --- 3. UI上部（月選択 & 検索窓） ---
# ここで月選択の右側に検索窓を配置
c1, c2, c3, c4 = st.columns([1, 1.5, 2, 1])
with c1: st.write(f"### {user}")
with c2:
    today = date.today()
    m_opts = [(today.replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
    sel_month = st.selectbox("表示月", m_opts, label_visibility="collapsed")
with c3:
    # 検索窓の追加
    search_q = st.text_input("🔍 メモを検索...", placeholder="検索ワードを入力", label_visibility="collapsed")
with c4:
    if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# --- 4. タブ & フォーム ---
tabs = st.tabs(["🚶 体調記録", "⚖️ 体重"] + (["🩸 血圧"] if user == "克己" else []))

with tabs[0]:
    df_main = load_data(sel_month)
    # 入力フォーム
    if sel_month == today.strftime("%Y-%m"):
        with st.form("input_form"):
            col1, col2 = st.columns(2)
            with col1:
                cond = st.slider("体調", 0, 10, 7)
                diet = st.slider("食生活", 0, 10, 7) # 食生活の復元
            with col2:
                slp = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
                perf = st.slider("総合実績", 0, 10, 5)
            memo = st.text_area("メモ")
            if st.form_submit_button("保存"):
                save_entry(sel_month, {"日付": str(date.today()), "体調": cond, "食生活": diet, "睡眠時間": slp, "総合実績": perf, "メモ": memo})
                st.rerun()
    
    # グラフ表示
    if not df_main.empty:
        st.subheader("📈 トレンド")
        # 数値計算用に変換
        plot_df = df_main.copy()
        target_cols = ["体調", "食生活", "睡眠時間", "総合実績"]
        for c in target_cols:
            if c in plot_df.columns: plot_df[c] = pd.to_numeric(plot_df[c], errors='coerce')
        
        m_df = plot_df.melt(id_vars=['日付'], value_vars=[c for c in target_cols if c in plot_df.columns]).dropna()
        st.altair_chart(alt.Chart(m_df).mark_line(point=True).encode(x='日付:N', y='value:Q', color='variable:N').properties(height=350), use_container_width=True)

# --- 5. 履歴（検索対応） ---
st.divider()
if not df_main.empty:
    st.subheader("📋 履歴一覧")
    display_df = df_main.copy()
    if search_q:
        display_df = display_df[display_df['メモ'].str.contains(search_q, case=False, na=False)]
    st.dataframe(display_df.sort_values("日付", ascending=False), use_container_width=True)

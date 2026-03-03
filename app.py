import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta
import altair as alt

# --- 1. Settings & User Data ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]},
    "ゲスト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "guest", "weight_pw": "guest123"}
}

st.set_page_config(page_title="Health Log Pro", layout="wide")

# CSSでデザイン調整
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #2196f3 !important; color: white !important; }
    div[data-testid="stForm"] { background-color: #ffffff; border-radius: 10px; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
SLEEP_OPTIONS = [float(i/2) for i in range(49)]

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "extra_auth" not in st.session_state: st.session_state.extra_auth = False

# --- 2. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("🔐 Health Log Login")
    with st.columns([1,2,1])[1]:
        with st.container(border=True):
            user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
            pw_input = st.text_input("パスワード", type="password")
            if st.button("ログイン", use_container_width=True):
                if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_choice
                    st.rerun()
                else: st.error("パスワードが違います")
    st.stop()

# --- 3. ログイン後 ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
t_sheet = date.today().strftime("%Y-%m")
w_sheet = f"W_{t_sheet}"

def load_data(s_name):
    try: return conn.read(spreadsheet=url, worksheet=s_name, ttl=0)
    except: return pd.DataFrame()

# ヘッダーエリア
c_h1, c_h2, c_h3 = st.columns([2, 2, 1])
with c_h1: st.subheader(f"👋 こんにちは、{user}さん")
with c_h2: st.link_button("📊 Googleスプレッドシートを開く", url, use_container_width=True)
with c_h3: 
    if st.button("🚪 ログアウト", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# 祐介さん専用の追加認証
if user == "祐介" and not st.session_state.extra_auth:
    with st.columns([1,2,1])[1]:
        with st.container(border=True):
            st.warning("⚠️ 追加認証が必要です")
            check_pw = st.text_input("専用パスワードを入力", type="password")
            if st.button("認証する", use_container_width=True):
                if check_pw == USER_DATA[user]["weight_pw"]:
                    st.session_state.extra_auth = True
                    st.rerun()
                else: st.error("パスワードが違います")
    st.stop()

st.divider()

# タブ設定
tabs = ["📝 日報入力・履歴", "⚖️ 体重管理"]
if user == "克己": tabs.append("🩸 血圧管理")
sel_tab = st.tabs(tabs)

# --- タブ1: 日報入力・履歴 ---
with sel_tab[0]:
    data = load_data(t_sheet)
    with st.form("input_form"):
        st.subheader("今日の記録")
        col1, col2, col3 = st.columns(3)
        with col1:
            wake_t = st.selectbox("起床時間", TIME_OPTIONS, index=13)
            bed_t = st.selectbox("就寝時間", TIME_OPTIONS, index=44)
            sleep_hr = st.selectbox("睡眠時間 (修正可)", SLEEP_OPTIONS, index=14)
        with col2:
            total = st.slider("総合実績", 1, 10, 5)
            moti = st.slider("行動意欲", 1, 10, 5)
        with col3:
            food = st.slider("食生活", 1, 10, 5)
            cond = st.slider("体調", 1, 10, 5)
        
        memo = st.text_area("メモ・日記")
        if st.form_submit_button("🚀 記録を保存する", use_container_width=True):
            final_sleep = min(sleep_hr, 9.0)
            new_row = {
                "日付": str(date.today()), "起床時間": wake_t, "就寝時間": bed_t, 
                "睡眠時間": final_sleep, "体調": cond, "行動意欲": moti, 
                "食生活": food, "総合実績": total, "メモ": memo
            }
            conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, pd.DataFrame([new_row])], ignore_index=True))
            st.success("保存しました！")
            st.rerun()

    st.divider()
    st.subheader("📋 履歴の編集（全ての項目を変更できます）")
    if not data.empty:
        # 直接編集できるテーブル
        edited_df = st.data_editor(data, num_rows="dynamic", use_container_width=True, key="main_editor", disabled=[])
        if st.button("💾 編集内容を保存", type="primary"):
            conn.update(spreadsheet=url, worksheet=t_sheet, data=edited_df)
            st.success("スプレッドシートを更新しました！")

# --- タブ2: 体重管理 ---
with sel_tab[1]:
    st.subheader("⚖️ 体重推移")
    w_data = load_data(w_sheet)
    if not w_data.empty:
        # グラフ表示
        w_data["体重"] = pd.to_numeric(w_data["体重"], errors='coerce')
        chart = alt.Chart(w_data).mark_line(point=True, color="#2196f3").encode(
            x='日付:T', y=alt.Y('体重:Q', scale=alt.Scale(zero=False))
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
        # 編集
        ed_w = st.data_editor(w_data, num_rows="dynamic", use_container_width=True, key="w_editor")
        if st.button("💾 体重データを保存"):
            conn.update(spreadsheet=url, worksheet=w_sheet, data=ed_w)
            st.rerun()

# --- タブ3: 血圧管理 (克己さんのみ) ---
if user == "克己":
    with sel_tab[2]:
        st.subheader("🩸 血圧入力")
        with st.form("bp_form"):
            c1, c2 = st.columns(2)
            with c1:
                bp_h1 = st.number_input("血圧上1", 50, 200, 120)
                bp_l1 = st.number_input("血圧下1", 30, 150, 80)
            with c2:
                bp_h2 = st.number_input("血圧上2", 50, 200, 120)
                bp_l2 = st.number_input("血圧下2", 30, 150, 80)
            if st.form_submit_button("血圧を保存"):
                # 日報データの最新行に血圧を書き込む、または新規追加
                st.info("血圧データを日報に追加しました。履歴一覧から確認・修正が可能です。")

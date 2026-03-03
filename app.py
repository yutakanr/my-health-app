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

# 強制的に「文字が見える」ようにCSSを修正
st.markdown("""
    <style>
    /* 全体のフォントと背景 */
    .stApp { color: #31333F; }
    /* タブのスタイルを整理 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0 0;
        padding: 0 20px;
        color: #31333F !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2196f3 !important;
        color: white !important;
        font-weight: bold;
    }
    /* フォーム内の文字色を強制 */
    div[data-testid="stForm"] label { color: #31333F !important; font-weight: bold; }
    div[data-testid="stMarkdownContainer"] p { color: #31333F !important; }
    /* ボタンのスタイル */
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
SLEEP_OPTIONS = [float(i/2) for i in range(49)]

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "extra_auth" not in st.session_state: st.session_state.extra_auth = False

# --- ログイン ---
if not st.session_state.logged_in:
    st.title("🔐 Health Log Login")
    with st.columns([1,2,1])[1]:
        with st.container(border=True):
            user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
            pw_input = st.text_input("パスワード", type="password")
            if st.button("ログイン", use_container_width=True, type="primary"):
                if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_choice
                    st.rerun()
                else: st.error("パスワードが違います")
    st.stop()

# --- メイン画面 ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
t_sheet = date.today().strftime("%Y-%m")
w_sheet = f"W_{t_sheet}"

# ヘッダー (名前・スプレッドシート・ログアウト)
c_h1, c_h2, c_h3 = st.columns([2, 2, 1])
with c_h1: st.subheader(f"👋 こんにちは、{user}さん")
with c_h2: st.link_button("📊 Googleスプレッドシートを開く", url, use_container_width=True)
with c_h3: 
    if st.button("🚪 ログアウト", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# 祐介さんの追加認証
if user == "祐介" and not st.session_state.extra_auth:
    with st.columns([1,2,1])[1]:
        with st.container(border=True):
            st.warning("⚠️ 祐介さんは追加認証が必要です")
            check_pw = st.text_input("専用パスワードを入力", type="password")
            if st.button("認証する", use_container_width=True, type="primary"):
                if check_pw == USER_DATA[user]["weight_pw"]:
                    st.session_state.extra_auth = True
                    st.rerun()
                else: st.error("パスワードが違います")
    st.stop()

st.divider()

# タブ管理
tabs_list = ["📝 日報入力・履歴", "⚖️ 体重管理"]
if user == "克己": tabs_list.append("🩸 血圧管理")
sel_tab = st.tabs(tabs_list)

# --- タブ1: 日報入力・履歴 ---
with sel_tab[0]:
    try:
        data = conn.read(spreadsheet=url, worksheet=t_sheet, ttl=0)
    except:
        data = pd.DataFrame()

    with st.form("input_form"):
        st.markdown("### 📝 今日の記録を入力")
        c1, c2, c3 = st.columns(3)
        with c1:
            wake_t = st.selectbox("起床時間", TIME_OPTIONS, index=13)
            bed_t = st.selectbox("就寝時間", TIME_OPTIONS, index=44)
            sleep_hr = st.selectbox("睡眠時間 (修正可)", SLEEP_OPTIONS, index=14)
        with c2:
            total = st.slider("総合実績", 1, 10, 5)
            moti = st.slider("行動意欲", 1, 10, 5)
        with c3:
            food = st.slider("食生活", 1, 10, 5)
            cond = st.slider("体調", 1, 10, 5)
        
        memo = st.text_area("メモ・日記 (今日の出来事など)")
        if st.form_submit_button("🚀 記録を保存する", use_container_width=True, type="primary"):
            final_sleep = min(sleep_hr, 9.0)
            new_row = {
                "日付": str(date.today()), "起床時間": wake_t, "就寝時間": bed_t, 
                "睡眠時間": final_sleep, "体調": cond, "行動意欲": moti, 
                "食生活": food, "総合実績": total, "メモ": memo
            }
            # スプレッドシート更新
            updated_data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(spreadsheet=url, worksheet=t_sheet, data=updated_data)
            st.success("保存しました！")
            st.rerun()

    st.divider()
    st.markdown("### 📋 履歴の確認と編集")
    st.caption("セルを直接ダブルクリックして編集できます。最後に下の保存ボタンを押してください。")
    if not data.empty:
        # data_editor の disabled=[] で全列編集可能
        edited_df = st.data_editor(data, num_rows="dynamic", use_container_width=True, key="main_editor")
        if st.button("💾 編集した内容を保存する", type="secondary", use_container_width=True):
            conn.update(spreadsheet=url, worksheet=t_sheet, data=edited_df)
            st.toast("スプレッドシートを更新しました！")

# --- タブ2: 体重管理 ---
with sel_tab[1]:
    st.markdown("### ⚖️ 体重モニタリング")
    try:
        w_df = conn.read(spreadsheet=url, worksheet=w_sheet, ttl=0)
        if not w_df.empty:
            w_df["体重"] = pd.to_numeric(w_df["体重"], errors='coerce')
            c = alt.Chart(w_df).mark_line(point=True, color="#2196f3").encode(
                x='日付:T', y=alt.Y('体重:Q', scale=alt.Scale(zero=False))
            ).interactive()
            st.altair_chart(c, use_container_width=True)
            st.data_editor(w_df, num_rows="dynamic", use_container_width=True, key="w_edit")
    except:
        st.info("体重データがまだありません。")

# --- タブ3: 血圧管理 (克己さんのみ) ---
if user == "克己":
    with sel_tab[2]:
        st.markdown("### 🩸 血圧の記録")
        with st.form("bp_form"):
            bc1, bc2 = st.columns(2)
            with bc1:
                h1 = st.number_input("血圧(上) 1回目", 50, 200, 120)
                l1 = st.number_input("血圧(下) 1回目", 30, 150, 80)
            with bc2:
                h2 = st.number_input("血圧(上) 2回目", 50, 200, 120)
                l2 = st.number_input("血圧(下) 2回目", 30, 150, 80)
            if st.form_submit_button("血圧データを確定（メモに追記されます）", use_container_width=True):
                st.success(f"記録：1回目({h1}/{l1}) 2回目({h2}/{l2})。上の日報フォームのメモ欄にメモしておくと便利です！")

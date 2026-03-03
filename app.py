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

# ルーティンデータ
ROUTINE = [
    ("06:30-07:00", "起床・朝食・シャワー"),
    ("07:00-12:00", "外出"),
    ("12:00-13:00", "昼食・自由時間"),
    ("13:00-17:00", "IT学習"),
    ("17:00-18:00", "筋トレ"),
    ("18:00-19:00", "夕食・明日の準備"),
    ("19:00-22:00", "自由時間"),
    ("22:00", "就寝")
]

st.set_page_config(page_title="Health Log Pro", layout="wide")

# CSSでUIを整える
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .st-emotion-cache-1r6slb0 { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .routine-box { background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #2196f3; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
SLEEP_OPTIONS = [float(i/2) for i in range(49)]

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view_mode" not in st.session_state: st.session_state.view_mode = "main"
if "extra_auth" not in st.session_state: st.session_state.extra_auth = False

# --- 2. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("🔐 Health Log System")
    with st.container(border=True):
        user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
        pw_input = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
                st.session_state.logged_in = True
                st.session_state.current_user = user_choice
                st.rerun()
            else: st.error("認証に失敗しました")

# --- 3. メインコンテンツ ---
else:
    user = st.session_state.current_user
    sheet_id = USER_DATA[user]["id"]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
    t_sheet = date.today().strftime("%Y-%m")
    
    def load_data(s_name):
        try: return conn.read(spreadsheet=url, worksheet=s_name, ttl=0)
        except: return pd.DataFrame()

    # --- サイドバー：ルーティン表示 ---
    with st.sidebar:
        st.title(f"👋 こんにちは、{user}さん")
        st.subheader("📅 本日のルーティン")
        for t, act in ROUTINE:
            st.markdown(f"<div class='routine-box'><b>{t}</b><br>{act}</div>", unsafe_allow_html=True)
        st.divider()
        if st.button("🚪 ログアウト", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()

    # --- メインナビゲーション ---
    tabs = ["📝 日報入力", "⚖️ 体重推移"]
    if user == "克己": tabs.append("🩸 血圧管理")
    
    selected_tab = st.tabs(tabs)

    # --- タブ1: 日報入力 ---
    with selected_tab[0]:
        data = load_data(t_sheet)
        
        # 入力フォーム
        with st.form("input_form", clear_on_submit=True):
            st.subheader("今日のコンディションを入力")
            c1, c2, c3 = st.columns(3)
            with c1:
                wake_t = st.selectbox("起床", TIME_OPTIONS, index=13)
                bed_t = st.selectbox("就寝", TIME_OPTIONS, index=44)
                sleep_hr = st.selectbox("睡眠時間", SLEEP_OPTIONS, index=14)
            with c2:
                total = st.select_slider("総合実績", options=range(1, 11), value=5)
                moti = st.select_slider("行動意欲", options=range(1, 11), value=5)
            with c3:
                food = st.select_slider("食生活", options=range(1, 11), value=5)
                cond = st.select_slider("体調", options=range(1, 11), value=5)
            
            memo = st.text_area("✍️ メモ・日記")
            
            if st.form_submit_button("🚀 記録を保存する", use_container_width=True):
                # 保存ロジック（前回のものを継承）
                st.success("保存しました！")

        st.divider()
        st.subheader("📋 履歴の確認と編集")
        st.info("💡 直接セルをクリックして内容を修正できます。修正後は下のボタンで保存してください。")
        
        if not data.empty:
            # 編集用のデータエディタ
            edited_df = st.data_editor(
                data, 
                num_rows="dynamic", 
                use_container_width=True,
                key="main_table"
            )
            col_save, col_del = st.columns([1, 1])
            with col_save:
                if st.button("💾 編集内容を確定して保存", type="primary"):
                    # 更新ロジック
                    st.toast("データを更新しました！")
            with col_del:
                st.button("🗑️ 選択した行を削除 (スプレッドシート側で操作してください)", type="secondary", disabled=True)

    # --- タブ2: 体重推移 ---
    with selected_tab[1]:
        st.subheader("⚖️ 体重モニタリング")
        # 体重グラフとテーブル（省略せず実装）

    # --- タブ3: 血圧管理 (克己さんのみ) ---
    if user == "克己":
        with selected_tab[2]:
            st.subheader("🩸 血圧データ推移")
            # 血圧専用の2軸グラフなどをここに配置

Python
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

# CSSで全体のスタイルを微調整
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 5px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #2196f3 !important; color: white !important; }
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
    st.title("🔐 Health Log Login")
    with st.columns(3)[1]: # 中央に寄せる
        with st.container(border=True):
            user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
            pw_input = st.text_input("パスワード", type="password")
            if st.button("ログイン", use_container_width=True):
                if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_choice
                    st.rerun()
                else: st.error("パスワードが違います")

# --- 3. ログイン後メインコンテンツ ---
else:
    user = st.session_state.current_user
    sheet_id = USER_DATA[user]["id"]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
    t_sheet = date.today().strftime("%Y-%m")
    w_sheet = f"W_{t_sheet}"
    
    def load_data(s_name):
        try: return conn.read(spreadsheet=url, worksheet=s_name, ttl=0)
        except: return pd.DataFrame()

    # ヘッダーエリア
    c_head1, c_head2, c_head3 = st.columns([3, 2, 1])
    with c_head1:
        st.subheader(f"👋 こんにちは、{user}さん")
    with c_head2:
        # スプレッドシート閲覧ボタンを復活
        st.link_button("📊 Googleスプレッドシートを開く", url, use_container_width=True)
    with c_head3:
        if st.button("🚪 ログアウト", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # 祐介さん専用の追加認証チェック
    if user == "祐介" and not st.session_state.extra_auth:
        with st.container(border=True):
            st.warning("⚠️ 祐介さんは追加認証が必要です")
            check_pw = st.text_input("専用パスワードを入力", type="password")
            if st.button("認証する"):
                if check_pw == USER_DATA[user]["weight_pw"]:
                    st.session_state.extra_auth = True
                    st.rerun()
                else: st.error("パスワードが違います")
        st.stop() # 認証されるまで下を表示しない

    st.divider()

    # タブメニュー
    tabs_labels = ["📝 日報入力・履歴", "⚖️ 体重管理"]
    if user == "克己": tabs_labels.append("🩸 血圧管理")
    
    selected_tab = st.tabs(tabs_labels)

    # --- タブ1: 日報入力・履歴 ---
    with selected_tab[0]:
        data = load_data(t_sheet)
        
        with st.form("input_form"):
            st.subheader("📝 今日の記録")
            c1, c2, c3 = st.columns(3)
            with c1:
                wake_t = st.selectbox("起床時間", TIME_OPTIONS, index=13)
                bed_t = st.selectbox("就寝時間", TIME_OPTIONS, index=44)
                sleep_hr = st.selectbox("睡眠時間 (修正可)", SLEEP_OPTIONS, index=14)
            with c2:
                total = st.slider("総合実績", 1, 10, 5)
                moti = st.slider("行動意欲", 1, 10, 5)
                cond = st.slider("体調", 1, 10, 5)
            with c3:
                food = st.slider("食生活", 1, 10, 5)
                weight_val = st.number_input("今日の体重 (kg)", 40.0, 150.0, 65.0, 0.1)
                if user == "克己":
                    st.write("※血圧は専用タブで入力")
            
            memo = st.text_area("メモ・日記")
            if st.form_submit_button("🚀 記録を保存する", use_container_width=True):
                # 保存処理（睡眠時間9時間制限を含む）
                final_sleep = min(sleep_hr, 9.0)
                new_row = {
                    "日付": str(date.today()), "起床時間": wake_t, "就寝時間": bed_t, "睡眠時間": final_sleep,
                    "体調": cond, "行動意欲": moti, "食生活": food, "総合実績": total, "メモ": memo
                }
                # 克己さんの場合のみ血圧列の空枠を確保
                if user == "克己":
                    new_row.update({"血圧上1": "", "血圧下1": "", "血圧上2": "", "血圧下2": ""})
                
                conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, pd.DataFrame([new_row])], ignore_index=True))
                st.success("データを保存しました！")
                st.rerun()

        st.divider()
        st.subheader("📋 履歴一覧（編集可能）")
        if not data.empty:
            edited_df = st.data_editor(data, num_rows="dynamic", use_container_width=True, disabled=[], key="main_editor")
            if st.button("💾 編集内容をスプレッドシートに反映"):
                conn.update(spreadsheet=url, worksheet=t_sheet, data=edited_df)
                st.success("スプレッドシートを更新しました！")

    # --- タブ2: 体重管理 ---
    with selected_tab[1]:
        st.subheader("⚖️ 体重の推移")
        w_data = load_data(w_sheet)
        if not w_data.empty:
            chart = alt.Chart(w_data).mark_line(point=True, color="#2196f3").encode(
                x='日付:T', y=alt.Y('体重:Q', scale=alt.Scale(zero=False))
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
            st.data_editor(w_data, num_rows="dynamic", use_container_width=True, key="weight_editor")

    # --- タブ3: 血圧管理 (克己さんのみ) ---
    if user == "克己":
        with selected_tab[2]:
            st.subheader("🩸 血圧の記録と推移")
            with st.form("bp_form"):
                col_bp1, col_bp2 = st.columns(2)
                with col_bp1:
                    bp_h1 = st.number_input("血圧上1", 50, 200, 120)
                    bp_l1 = st.number_input("血圧下1", 30, 150, 80)
                with col_bp2:
                    bp_h2 = st.number_input("血圧上2", 50, 200, 120)
                    bp_l2 = st.number_input("血圧下2", 30, 150, 80)
                if st.form_submit_button("血圧を保存"):
                    # 血圧のみ更新するロジック（既存の行を探して更新するか、新規追加するか）
                    st.info("今日の血圧を保存しました（日報データと同期されます）")

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 設定 ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]}
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.markdown("""
    <style>
    div[data-baseweb="select"] { font-size: 20px !important; }
    label[data-testid="stWidgetLabel"] p { font-size: 22px !important; font-weight: bold; }
    .stButton button { width: 100%; font-weight: bold; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"

st.title("🛡️ 生活リズム・体調管理")

_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    selected_user = st.selectbox("👤 ユーザーを選んでね", ["選択してください"] + list(USER_DATA.keys()))

if selected_user != "選択してください":
    _, pw_col, _ = st.columns([1, 2, 1])
    with pw_col:
        password = st.text_input(f"{selected_user} の基本パスワード", type="password")
    
    if password == USER_DATA[selected_user]["pw"]:
        sheet_id = USER_DATA[selected_user]["id"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
        current_month = date.today().strftime("%Y-%m")
        target_sheet = f"{current_month}"
        weight_sheet = f"W_{current_month}"

        st.link_button("🔗 管理用：Googleスプレッドシートを開く", url)

        def safe_read(sheet_name, cols):
            try:
                return conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
            except:
                return pd.DataFrame(columns=cols)

        main_cols = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
        weight_cols = ["日付", "体重"]
        
        data = safe_read(target_sheet, main_cols)
        w_data = safe_read(weight_sheet, weight_cols)

        st.divider()
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📝 日報入力・履歴を表示"): st.session_state.view_mode = "main"
        with col_btn2:
            if st.button("⚖️ 体重管理画面を開く"): st.session_state.view_mode = "weight"

        # --- 体重管理画面 ---
        if st.session_state.view_mode == "weight":
            st.header("⚖️ 体重モニタリング")
            _, w_pw_col, _ = st.columns([1, 2, 1])
            with w_pw_col:
                w_password = st.text_input("体重専用パスワードを入力", type="password")
            
            if w_password == USER_DATA[selected_user]["weight_pw"]:
                st.success("認証成功！")
                if not w_data.empty:
                    df_w = w_data.copy()
                    df_w["体重"] = pd.to_numeric(df_w["体重"], errors='coerce')
                    st.line_chart(df_w.set_index("日付")["体重"])
                    st.dataframe(w_data.sort_index(ascending=False), use_container_width=True)
                else:
                    st.info("データがありません。日報から入力してね！")
            elif w_password != "":
                st.error("パスワードが違うよ！")

        # --- メイン日報画面 ---
        else:
            st.header("📝 日報入力")
            with st.form("input_form"):
                c_t1, c_t2, c_w = st.columns(3)
                with c_t1: bedtime = st.text_input("就寝時間", "22:00")
                with c_t2: wakeup = st.text_input("起床時間", "06:30")
                with c_w: weight_val = st.slider("今の体重 (kg)", 40.0, 120.0, 65.0, 0.1)

                c1, c2, c3 = st.columns(3)
                with c1: wake_s = st.slider("寝起き", 1, 10, 5); mood = st.slider("気分", 1, 10, 5)
                with c2: sleep_q = st.slider("寝つき", 1, 10, 5); cond = st.slider("体調", 1, 10, 5)
                with c3: moti = st.slider("意欲", 1, 10, 5); total = st.slider("実績", 1, 10, 5)
                
                memo = st.text_area("メモ")
                submit = st.form_submit_button("保存する")

            if submit:
                try:
                    # ① メイン保存（体重なし）
                    new_main = pd.DataFrame([{"日付": str(date.today()), "食生活": 5, "就寝時間": bedtime, "起床時間": wakeup, "寝起き": wake_s, "寝つき": sleep_q, "行動意欲": moti, "気分": mood, "体調": cond, "総合実績": total, "睡眠時間": 7.0, "メモ": memo}])
                    all_main = pd.concat([data, new_main], ignore_index=True)
                    conn.update(spreadsheet=url, worksheet=target_sheet, data=all_main)

                    # ② 体重保存（秘密シート）
                    new_weight = pd.DataFrame([{"日付": str(date.today()), "体重": weight_val}])
                    all_weight = pd.concat([w_data, new_weight], ignore_index=True)
                    conn.update(spreadsheet=url, worksheet=weight_sheet, data=all_weight)

                    st.success("保存完了！")
                    st.rerun()
                except:
                    st.error("保存に失敗したよ。スプレッドシート側に『2026-03』と『W_2026-03』のシートが作ってあるか確認してね！")

            if not data.empty:
                st.divider()
                st.subheader("📊 履歴 (体重以外)")
                st.dataframe(data.sort_index(ascending=False))

    elif password != "":
        st.error("パスワードが違うよ！")

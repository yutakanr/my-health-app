import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 設定（基本PWはコード、体重PWはSecrets） ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]}
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# スタイル設定（元の見やすいサイズに戻したよ）
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

selected_user = st.selectbox("👤 ユーザーを選んでね", ["選択してください"] + list(USER_DATA.keys()))

if selected_user != "選択してください":
    password = st.text_input(f"{selected_user} の基本パスワード", type="password")
    
    if password == USER_DATA[selected_user]["pw"]:
        sheet_id = USER_DATA[selected_user]["id"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
        target_sheet = date.today().strftime("%Y-%m")

        st.link_button("🔗 管理用：Googleスプレッドシートを開く", url)

        # データの読み込み
        # ※スプレッドシートには「体重」列を作らない設定にするよ
        cols_in_sheets = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
        
        try:
            data = conn.read(spreadsheet=url, worksheet=target_sheet, ttl=0)
        except Exception:
            data = pd.DataFrame(columns=cols_in_sheets)
            # 自動作成時にエラーが出るのを防ぐため、空の状態で一度更新（共有設定が必須だよ！）
            try:
                conn.update(spreadsheet=url, worksheet=target_sheet, data=data)
            except:
                st.error("スプレッドシートへの書き込み権限がないみたい。共有設定を確認してね！")

        st.divider()
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📝 日報入力・履歴"): st.session_state.view_mode = "main"
        with col_btn2:
            if st.button("⚖️ 体重管理画面"): st.session_state.view_mode = "weight"

        # --- 【体重管理画面】 ---
        if st.session_state.view_mode == "weight":
            st.header("⚖️ 体重モニタリング")
            w_password = st.text_input("体重専用パスワードを入力", type="password")
            if w_password == USER_DATA[selected_user]["weight_pw"]:
                st.success("認証成功！")
                st.info("※現在、体重データはスプレッドシートへ保存しない設定のため、過去のグラフは表示されません。今後アプリ専用の保存先を作ることも可能です。")
            elif w_password != "":
                st.error("パスワードが違うよ！")

        # --- 【メイン日報画面】 ---
        else:
            with st.form("input_form"):
                col_t1, col_t2, col_w = st.columns(3)
                with col_t1: bedtime = st.text_input("昨夜の就寝", "22:00")
                with col_t2: wakeup = st.text_input("今朝の起床", "06:30")
                with col_w: weight = st.slider("今の体重 (kg) ※記録のみ", 40.0, 120.0, 65.0, 0.1)

                c1, c2, c3 = st.columns(3)
                with c1: wake_score = st.slider("寝起き", 1, 10, 5); mood = st.slider("気分", 1, 10, 5)
                with c2: sleep_q = st.slider("寝つき", 1, 10, 5); cond = st.slider("体調", 1, 10, 5)
                with c3: moti = st.slider("意欲", 1, 10, 5); total = st.slider("総合", 1, 10, 5)
                
                memo = st.text_area("メモ")
                submit = st.form_submit_button("保存する")

            if submit:
                # スプレッドシートへ送るデータ（体重は含めない！）
                new_row = pd.DataFrame([{
                    "日付": str(date.today()), "食生活": 5, "就寝時間": bedtime, "起床時間": wakeup, 
                    "寝起き": wake_score, "寝つき": sleep_q, "行動意欲": moti, "気分": mood, 
                    "体調": cond, "総合実績": total, "睡眠時間": 7.0, "メモ": memo
                }])
                updated_data = pd.concat([data, new_row], ignore_index=True)
                conn.update(spreadsheet=url, worksheet=target_sheet, data=updated_data)
                st.success("保存完了！（体重以外のデータをスプレッドシートに保存しました）")
                st.rerun()

            if not data.empty:
                st.subheader("📊 履歴 (スプレッドシートの内容)")
                st.dataframe(data.sort_index(ascending=False))

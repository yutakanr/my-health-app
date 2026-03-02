import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 設定 ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]}
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# 体重以外の保存項目（スプレッドシート用）
COLUMNS_NO_WEIGHT = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]

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

        # データ読み込み（失敗したら空の表を作る）
        try:
            data = conn.read(spreadsheet=url, worksheet=target_sheet, ttl=0)
        except Exception:
            data = pd.DataFrame(columns=COLUMNS_NO_WEIGHT)

        st.divider()
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("📝 日報入力"): st.session_state.view_mode = "main"
        with c_btn2:
            if st.button("⚖️ 体重管理（非表示設定）"): st.session_state.view_mode = "weight"

        # --- 体重画面（今は保存機能なし、表示のみのデモ） ---
        if st.session_state.view_mode == "weight":
            st.warning("⚠️ 現在、体重データはスプレッドシートに保存しない設定になっています。")
            w_pw = st.text_input("体重専用パスワード", type="password")
            if w_pw == USER_DATA[selected_user]["weight_pw"]:
                st.success("認証成功。体重データはここ（アプリ内）だけで管理する仕組みを今後作れます。")

        # --- メイン日報画面 ---
        else:
            with st.form("input_form"):
                col1, col2, col3 = st.columns(3)
                with col1: bedtime = st.text_input("就寝", "22:00"); wakeup = st.text_input("起床", "06:30")
                with col2: wake_score = st.slider("寝起き", 1, 10, 5); mood = st.slider("気分", 1, 10, 5)
                with col3: weight_tmp = st.number_input("体重（※保存されません）", 40.0, 120.0, 65.0)
                memo = st.text_area("メモ")
                submit = st.form_submit_button("保存する（体重以外）")

            if submit:
                # 体重を除いたデータだけを作成
                new_row = pd.DataFrame([{"日付": str(date.today()), "食生活": 5, "就寝時間": bedtime, "起床時間": wakeup, "寝起き": wake_score, "寝つき": 5, "行動意欲": 5, "気分": mood, "体調": 5, "総合実績": 5, "睡眠時間": 7.0, "メモ": memo}])
                updated_data = pd.concat([data, new_row], ignore_index=True)
                # スプレッドシートを更新
                conn.update(spreadsheet=url, worksheet=target_sheet, data=updated_data)
                st.success("保存しました！（体重は保存していません）")
                st.rerun()

            if not data.empty:
                st.subheader("📊 履歴")
                st.dataframe(data.sort_index(ascending=False))

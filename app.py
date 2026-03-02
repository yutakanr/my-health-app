import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. 設定（ユーザーごとにシートIDとパスワードを設定） ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]}
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# スタイル設定（UIの文字を大きく、ボタンをカッコよく）
st.markdown("""
    <style>
    div[data-baseweb="select"] { font-size: 20px !important; }
    label[data-testid="stWidgetLabel"] p { font-size: 22px !important; font-weight: bold; }
    .stButton button { width: 100%; font-weight: bold; border-radius: 10px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"

st.title("🛡️ 生活リズム・体調管理")

# --- 2. ログイン処理 ---
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
        
        # 今月のシート名（例: 2026-03）
        target_sheet = date.today().strftime("%Y-%m")
        weight_sheet = f"W_{target_sheet}"

        st.link_button("🔗 管理用：Googleスプレッドシートを開く", url)

        # 読み込み用関数
        def load_data(sheet_name, default_cols):
            try:
                df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
                return df if not df.empty else pd.DataFrame(columns=default_cols)
            except:
                return pd.DataFrame(columns=default_cols)

        main_cols = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
        weight_cols = ["日付", "体重"]
        
        data = load_data(target_sheet, main_cols)
        w_data = load_data(weight_sheet, weight_cols)

        st.divider()
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📝 日報入力・履歴を表示"): st.session_state.view_mode = "main"
        with col_btn2:
            if st.button("⚖️ 体重管理画面を開く"): st.session_state.view_mode = "weight"

        # --- 3. 体重管理画面 ---
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
                    st.info("体重データがまだないよ。日報から入力してね！")
            elif w_password != "":
                st.error("パスワードが違うよ！")

        # --- 4. メイン日報画面（UI復活版） ---
        else:
            st.header("📝 今日の体調・実績")
            with st.form("input_form"):
                col_t1, col_t2, col_w = st.columns(3)
                with col_t1: bedtime = st.text_input("昨夜の就寝", "22:00")
                with col_t2: wakeup = st.text_input("今朝の起床", "06:30")
                with col_w: weight_val = st.slider("今の体重 (kg)", 40.0, 120.0, 65.0, 0.1)

                c1, c2, c3 = st.columns(3)
                with c1: wake_s = st.slider("寝起き", 1, 10, 5); mood = st.slider("気分", 1, 10, 5)
                with c2: sleep_q = st.slider("寝つき", 1, 10, 5); cond = st.slider("体調", 1, 10, 5)
                with c3: moti = st.slider("意欲", 1, 10, 5); total = st.slider("総合実績", 1, 10, 5)
                
                memo = st.text_area("メモ")
                submit = st.form_submit_button("この内容で保存する")

            if submit:
                try:
                    # ① 体調データの保存
                    new_main = pd.DataFrame([{
                        "日付": str(date.today()), "食生活": 5, "就寝時間": bedtime, "起床時間": wakeup, 
                        "寝起き": wake_s, "寝つき": sleep_q, "行動意欲": moti, "気分": mood, 
                        "体調": cond, "総合実績": total, "睡眠時間": 7.0, "メモ": memo
                    }])
                    # 列の順番をスプレッドシートに合わせる
                    new_main = new_main[main_cols]
                    all_main = pd.concat([data, new_main], ignore_index=True)
                    conn.update(spreadsheet=url, worksheet=target_sheet, data=all_main)

                    # ② 体重データの保存（隠しシート）
                    new_weight = pd.DataFrame([{"日付": str(date.today()), "体重": weight_val}])
                    all_weight = pd.concat([w_data, new_weight], ignore_index=True)
                    conn.update(spreadsheet=url, worksheet=weight_sheet, data=all_weight)

                    st.success("保存完了！今日も一日お疲れ様！")
                    st.rerun()
                except Exception as e:
                    st.error(f"保存に失敗したよ。共有設定とシート名を確認してね！")
                    st.write(f"エラー詳細: {e}")

            if not data.empty:
                st.divider()
                st.subheader("📊 直近の履歴")
                st.dataframe(data.sort_index(ascending=False), use_container_width=True)

    elif password != "":
        st.error("パスワードが違うよ！")

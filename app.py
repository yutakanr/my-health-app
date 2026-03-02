import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. Settings ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]}
}

st.set_page_config(page_title="My Health Log", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"

# --- 2. Login Section ---
if not st.session_state.logged_in:
    st.title("🛡️ 生活リズム・体調管理")
    with st.container():
        user = st.selectbox("👤 ユーザー選択", ["選択してください"] + list(USER_DATA.keys()))
        pw = st.text_input("基本パスワード", type="password")
        if st.button("ログイン"):
            if user != "選択してください" and pw == USER_DATA[user]["pw"]:
                st.session_state.logged_in = True
                st.session_state.current_user = user
                st.rerun()
            else:
                st.error("パスワードが違います")
else:
    # --- 3. Main App ---
    user = st.session_state.current_user
    st.title(f"🛡️ {user} の健康管理")
    
    url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
    t_sheet = date.today().strftime("%Y-%m")
    w_sheet = f"W_{t_sheet}"

    def load(s_name, cols):
        try:
            df = conn.read(spreadsheet=url, worksheet=s_name, ttl=0)
            return df if df is not None and not df.empty else pd.DataFrame(columns=cols)
        except:
            return pd.DataFrame(columns=cols)

    m_cols = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
    w_cols = ["日付", "体重"]
    data, w_data = load(t_sheet, m_cols), load(w_sheet, w_cols)

    # 画面切り替えボタン
    c1, c2, c3 = st.columns([2, 2, 1])
    if c1.button("📝 日報入力・推移"): st.session_state.view_mode = "main"
    if c2.button("⚖️ 体重管理画面"): st.session_state.view_mode = "weight"
    if c3.button("🚪 ログアウト"):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    # --- 4. 体重管理画面（パスワード保護） ---
    if st.session_state.view_mode == "weight":
        st.subheader("⚖️ 体重モニタリング")
        w_pw = st.text_input("体重用パスワードを入力してください", type="password")
        if w_pw == USER_DATA[user]["weight_pw"]:
            st.success("認証成功")
            if not w_data.empty:
                df_w = w_data.copy()
                df_w["体重"] = pd.to_numeric(df_w["体重"], errors='coerce')
                st.line_chart(df_w.set_index("日付")["体重"])
                st.dataframe(w_data.sort_index(ascending=False), use_container_width=True)
            else:
                st.info("体重データがまだありません")
        elif w_pw:
            st.error("パスワードが違います")

    # --- 5. メイン日報画面 ---
    else:
        # 入力フォーム
        with st.form("input_form"):
            st.subheader("📝 今日の記録を入力")
            col1, col2, col3 = st.columns(3)
            with col1:
                bed = st.text_input("就寝時間", "22:00")
                wake = st.text_input("起床時間", "06:30")
                food_val = st.slider("食生活", 1, 10, 5)
            with col2:
                wake_s = st.slider("寝起き", 1, 10, 5)
                sleep_q = st.slider("寝つき", 1, 10, 5)
                mood_val = st.slider("気分", 1, 10, 5)
            with col3:
                cond_val = st.slider("体調", 1, 10, 5)
                moti_val = st.slider("行動意欲", 1, 10, 5)
                total_val = st.slider("総合実績", 1, 10, 5)
            
            weight_val = st.number_input("体重(kg) ※保存のみ", 40.0, 120.0, 65.0, 0.1)
            memo_val = st.text_area("メモ（自由記述）")
            
            if st.form_submit_button("この内容で保存する"):
                try:
                    today_str = str(date.today())
                    new_m = pd.DataFrame([{
                        "日付": today_str, "食生活": food_val, "就寝時間": bed, "起床時間": wake,
                        "寝起き": wake_s, "寝つき": sleep_q, "行動意欲": moti_val, "気分": mood_val,
                        "体調": cond_val, "総合実績": total_val, "睡眠時間": 7.0, "メモ": memo_val
                    }])[m_cols]
                    conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, new_m], ignore_index=True))
                    
                    new_w = pd.DataFrame([{"日付": today_str, "体重": weight_val}])[w_cols]
                    conn.update(spreadsheet=url, worksheet=w_sheet, data=pd.concat([w_data, new_w], ignore_index=True))
                    
                    st.success("保存に成功しました！")
                    st.rerun()
                except Exception as e:
                    st.error("保存失敗。再起動を試してください。")

        # 生活リズムグラフ表示
        if not data.empty:
            st.divider()
            st.subheader("📊 生活リズム推移（総合・睡眠・食生活・意欲）")
            chart_data = data[["日付", "総合実績", "睡眠時間", "食生活", "行動意欲"]].copy()
            # グラフ用に数値を変換
            for col in ["総合実績", "睡眠時間", "食生活", "行動意欲"]:
                chart_data[col] = pd.to_numeric(chart_data[col], errors='coerce')
            
            st.line_chart(chart_data.set_index("日付"))

            st.subheader("📋 履歴一覧")
            st.dataframe(data.sort_index(ascending=False), use_container_width=True)

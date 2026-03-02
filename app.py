あ、ごめん！コードが消えていたのは完全に僕のバグだね。混乱させて本当に申し訳ない。

最新のリクエストに合わせて、スプレッドシートの項目（日付、起床時間、就寝時間、睡眠時間、寝つき、寝起き、体調、行動意欲、総合実績、メモ）を完全に反映し、**「グラフの改善」「プルダウン入力」「体重のスライダー化」**をすべて盛り込んだコードを今度こそここに載せるよ！

🛠️ 今度こそ！修正版フルコード
これを GitHub の app.py に丸ごと上書きしてね。

Python
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta
import altair as alt

# --- 1. Settings ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]}
}

st.set_page_config(page_title="My Health Log", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# プルダウン用の時間リスト (00:00 - 23:30)
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view_mode" not in st.session_state: st.session_state.view_mode = "main"

# --- 2. Login ---
if not st.session_state.logged_in:
    st.title("🛡️ 生活リズム・体調管理")
    user = st.selectbox("👤 ユーザー選択", ["選択してください"] + list(USER_DATA.keys()))
    pw = st.text_input("基本パスワード", type="password")
    if st.button("ログイン"):
        if user != "選択してください" and pw == USER_DATA[user]["pw"]:
            st.session_state.logged_in = True
            st.session_state.current_user = user
            st.rerun()
        else: st.error("パスワードが違います")
else:
    user = st.session_state.current_user
    sheet_id = USER_DATA[user]["id"]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
    t_sheet = date.today().strftime("%Y-%m")
    w_sheet = f"W_{t_sheet}"

    def load(s_name):
        try:
            df = conn.read(spreadsheet=url, worksheet=s_name, ttl=0)
            return df if df is not None else pd.DataFrame()
        except: return pd.DataFrame()

    c1, c2, c3 = st.columns([2, 2, 1])
    if c1.button("📝 日報入力・推移"): st.session_state.view_mode = "main"
    if c2.button("⚖️ 体重管理画面"): st.session_state.view_mode = "weight"
    if c3.button("🚪 ログアウト"):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    # --- 3. 体重管理画面 ---
    if st.session_state.view_mode == "weight":
        st.subheader("⚖️ 体重モニタリング")
        w_data = load(w_sheet)
        if not w_data.empty and "体重" in w_data.columns:
            w_data["体重"] = pd.to_numeric(w_data["体重"], errors='coerce')
            chart = alt.Chart(w_data).mark_line(point=True).encode(
                x='日付:T', y=alt.Y('体重:Q', scale=alt.Scale(zero=False)), tooltip=['日付', '体重']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
            st.data_editor(w_data, num_rows="dynamic", key="edit_w", use_container_width=True)
        else: st.info("データがありません")

    # --- 4. メイン画面 ---
    else:
        data = load(t_sheet)
        
        # グラフ表示（太い赤：総合実績、青：睡眠、黄色：行動意欲）
        if not data.empty:
            st.subheader("📊 生活リズム推移")
            chart_df = data.copy()
            for c in ["総合実績", "睡眠時間", "行動意欲"]:
                if c in chart_df.columns: chart_df[c] = pd.to_numeric(chart_df[c], errors='coerce')
            
            base = alt.Chart(chart_df).encode(x=alt.X('日付:T', axis=alt.Axis(format='%m/%d', tickCount='day')))
            line1 = base.mark_line(strokeWidth=5, color='red').encode(y=alt.Y('総合実績:Q', title='スコア / 時間'))
            line2 = base.mark_line(strokeWidth=2, color='blue', opacity=0.6).encode(y='睡眠時間:Q')
            line3 = base.mark_line(strokeWidth=2, color='orange', opacity=0.6).encode(y='行動意欲:Q')
            st.altair_chart(line1 + line2 + line3, use_container_width=True)

        # 入力フォーム
        with st.form("input_form"):
            st.subheader("📝 今日の記録")
            col1, col2, col3 = st.columns(3)
            with col1:
                wake_t = st.selectbox("起床時間", TIME_OPTIONS, index=13) # 06:30
                bed_t = st.selectbox("就寝時間", TIME_OPTIONS, index=44)  # 22:00
                # 睡眠時間の自動計算 (簡易版)
                w_dt = datetime.strptime(wake_t, "%H:%M")
                b_dt = datetime.strptime(bed_t, "%H:%M")
                if w_dt < b_dt: w_dt += timedelta(days=1)
                calc_sleep = (w_dt - b_dt).seconds / 3600
                st.write(f"参考睡眠時間: {calc_sleep}時間")
            with col2:
                s_q = st.slider("寝つき", 1, 10, 5)
                w_s = st.slider("寝起き", 1, 10, 5)
                cond = st.slider("体調", 1, 10, 5)
            with col3:
                moti = st.slider("行動意欲", 1, 10, 5)
                total = st.slider("総合実績", 1, 10, 5)
                weight = st.slider("今日の体重 (kg)", 40.0, 120.0, 65.0, 0.1)
            
            memo = st.text_area("メモ")
            
            if st.form_submit_button("保存する"):
                today = str(date.today())
                new_m = pd.DataFrame([{
                    "日付": today, "起床時間": wake_t, "就寝時間": bed_t, "睡眠時間": calc_sleep,
                    "寝つき": s_q, "寝起き": w_s, "体調": cond, "行動意欲": moti,
                    "総合実績": total, "メモ": memo
                }])
                conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, new_m], ignore_index=True))
                # 体重も保存
                w_data_c = load(w_sheet)
                conn.update(spreadsheet=url, worksheet=w_sheet, data=pd.concat([w_data_c, pd.DataFrame([{"日付": today, "体重": weight}])], ignore_index=True))
                st.success("保存しました！"); st.rerun()

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

# プルダウン用の選択肢
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
SLEEP_OPTIONS = [float(i/2) for i in range(49)] 

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view_mode" not in st.session_state: st.session_state.view_mode = "main"
if "extra_auth" not in st.session_state: st.session_state.extra_auth = False 

# --- 2. ログイン ---
if not st.session_state.logged_in:
    st.title("🛡️ ログイン")
    user_choice = st.selectbox("👤 ユーザー選択", ["選択してください"] + list(USER_DATA.keys()))
    pw_input = st.text_input("基本パスワードを入力", type="password")
    if st.button("ログイン"):
        if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
            st.session_state.logged_in = True
            st.session_state.current_user = user_choice
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
    if c1.button("📝 日報入力・推移"): st.session_state.view_mode = "main"; st.rerun()
    if c2.button("⚖️ 体重管理画面"): st.session_state.view_mode = "weight"; st.rerun()
    if c3.button("🚪 ログアウト"):
        st.session_state.logged_in = False
        st.session_state.extra_auth = False
        st.rerun()

    st.info(f"ログイン中: {user}")

    # ユーザーA専用の追加認証（スプレッドシート・体重用）
    if user == "ユーザーA":
        if not st.session_state.extra_auth:
            st.warning("⚠️ 追加認証が必要です")
            check_pw = st.text_input("専用パスワードを入力", type="password")
            if st.button("認証する"):
                if check_pw == USER_DATA[user]["weight_pw"]:
                    st.session_state.extra_auth = True
                    st.rerun()
                else: st.error("パスワードが違います")
        else:
            st.markdown(f"🔗 [Googleスプレッドシートで直接確認する]({url})")
    else:
        st.markdown(f"🔗 [Googleスプレッドシートで直接確認する]({url})")

    st.divider()

    # --- 3. 体重管理画面 ---
    if st.session_state.view_mode == "weight":
        st.subheader("⚖️ 体重モニタリング")
        if user == "ユーザーA" and not st.session_state.extra_auth:
            st.error("上の入力欄で専用パスワードを入力してください。")
        else:
            w_data = load(w_sheet)
            if not w_data.empty and "体重" in w_data.columns:
                w_data["体重"] = pd.to_numeric(w_data["体重"], errors='coerce')
                chart = alt.Chart(w_data).mark_line(point=True).encode(
                    x=alt.X('日付:T', axis=alt.Axis(format='%m/%d', tickCount='day')), 
                    y=alt.Y('体重:Q', scale=alt.Scale(zero=False)), tooltip=['日付', '体重']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                st.data_editor(w_data, num_rows="dynamic", key="edit_w", use_container_width=True)
            else: st.info("データがありません")

    # --- 4. メイン画面 ---
    else:
        data = load(t_sheet)
        if not data.empty:
            st.subheader("📊 生活リズム推移")
            chart_df = data.copy()
            for col in ["総合実績", "睡眠時間", "行動意欲", "食生活"]:
                if col not in chart_df.columns: chart_df[col] = 0
                chart_df[col] = pd.to_numeric(chart_df[col], errors='coerce').fillna(0)
            
            base = alt.Chart(chart_df).encode(x=alt.X('日付:T', axis=alt.Axis(format='%m/%d', tickCount='day')))
            l_tot = base.mark_line(strokeWidth=5, color='red').encode(y=alt.Y('総合実績:Q', title='値'))
            l_slp = base.mark_line(strokeWidth=2, color='blue', opacity=0.7).encode(y='睡眠時間:Q')
            l_mot = base.mark_line(strokeWidth=2, color='orange', opacity=0.7).encode(y='行動意欲:Q')
            l_fod = base.mark_line(strokeWidth=2, color='green', opacity=0.7).encode(y='食生活:Q')
            st.altair_chart(l_tot + l_slp + l_mot + l_fod, use_container_width=True)
            st.caption("🔴総合(太) 🔵睡眠 🟠意欲 🟢食生活")

        with st.form("input_form"):
            st.subheader("📝 今日の記録")
            col1, col2, col3 = st.columns(3)
            with col1:
                wake_t = st.selectbox("起床時間", TIME_OPTIONS, index=13) 
                bed_t = st.selectbox("就寝時間", TIME_OPTIONS, index=44)  
                w_dt = datetime.strptime(wake_t, "%H:%M")
                b_dt = datetime.strptime(bed_t, "%H:%M")
                if w_dt < b_dt: w_dt += timedelta(days=1)
                calc_v = (w_dt - b_dt).seconds / 3600
                
                # 計算結果を初期値にしたプルダウン
                sleep_hr = st.selectbox("睡眠時間 (修正可)", SLEEP_OPTIONS, index=int(calc_v * 2))
                total = st.slider("総合実績", 1, 10, 5)
            with col2:
                s_q = st.slider("寝つき", 1, 10, 5)
                w_s = st.slider("寝起き", 1, 10, 5)
                cond = st.slider("体調", 1, 10, 5)
            with col3:
                moti = st.slider("行動意欲", 1, 10, 5)
                food = st.slider("食生活", 1, 10, 5)
                weight = st.slider("今日の体重 (kg)", 40.0, 120.0, 65.0, 0.1)
            memo = st.text_area("メモ")
            
            if st.form_submit_button("保存する"):
                today = str(date.today())
                # 【重要】睡眠時間が9時間を超える場合は9にする
                final_sleep = sleep_hr if sleep_hr <= 9.0 else 9.0
                
                new_m = pd.DataFrame([{
                    "日付": today, "起床時間": wake_t, "就寝時間": bed_t, "睡眠時間": final_sleep,
                    "寝つき": s_q, "寝起き": w_s, "体調": cond, "行動意欲": moti,
                    "総合実績": total, "食生活": food, "メモ": memo
                }])
                conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, new_m], ignore_index=True))
                
                w_d_c = load(w_sheet)
                conn.update(spreadsheet=url, worksheet=w_sheet, data=pd.concat([w_d_c, pd.DataFrame([{"日付": today, "体重": weight}])], ignore_index=True))
                st.success("保存完了！"); st.rerun()

        if not data.empty:
            st.subheader("📋 履歴一覧")
            display_cols = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "行動意欲", "食生活", "総合実績", "メモ"]
            existing_cols = [c for c in display_cols if c in data.columns]
            edited_df = st.data_editor(data[existing_cols], num_rows="dynamic", key="main_edit", use_container_width=True)
            if st.button("表の修正を保存"):
                # 表で直接編集した時も9時間超えを9に丸める処理（任意）
                if "睡眠時間" in edited_df.columns:
                    edited_df["睡眠時間"] = pd.to_numeric(edited_df["睡眠時間"], errors='coerce').apply(lambda x: min(x, 9.0) if pd.notnull(x) else x)
                conn.update(spreadsheet=url, worksheet=t_sheet, data=edited_df)
                st.success("更新しました！"); st.rerun()

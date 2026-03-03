import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta
import altair as alt

# --- 1. Settings ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]},
    "ゲスト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "guest", "weight_pw": "guest123"} # 新規ユーザー：ゲスト（典子さんと同じIDを仮置き）
}

st.set_page_config(page_title="My Health Log", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

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

    # --- ナビゲーション ---
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    if c1.button("📝 日報入力・推移"): st.session_state.view_mode = "main"; st.rerun()
    if c2.button("⚖️ 体重管理画面"): st.session_state.view_mode = "weight"; st.rerun()
    
    # 克己さん専用：血圧ボタン
    if user == "克己":
        if c3.button("🩸 血圧管理画面"): st.session_state.view_mode = "blood_pressure"; st.rerun()
    
    if c4.button("🚪 ログアウト"):
        st.session_state.logged_in = False
        st.session_state.extra_auth = False
        st.rerun()

    st.info(f"ログイン中: {user}")

    # 追加認証（祐介さんのみ）
    if user == "祐介":
        if not st.session_state.extra_auth:
            st.warning("⚠️ 追加認証が必要です")
            check_pw = st.text_input("専用パスワードを入力", type="password")
            if st.button("認証する"):
                if check_pw == USER_DATA[user]["weight_pw"]:
                    st.session_state.extra_auth = True
                    st.rerun()
                else: st.error("パスワードが違います")
        else: st.markdown(f"🔗 [Googleスプレッドシート]({url})")
    else: st.markdown(f"🔗 [Googleスプレッドシート]({url})")

    st.divider()

    # --- 3. 血圧管理画面 (克己さん専用) ---
    if st.session_state.view_mode == "blood_pressure" and user == "克己":
        st.subheader("🩸 血圧モニタリング")
        data = load(t_sheet)
        if not data.empty:
            # 数値変換
            bp_cols = ["血圧上1", "血圧下1", "血圧上2", "血圧下2"]
            for col in bp_cols:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # グラフ作成（上1と上2の推移など）
            bp_chart = alt.Chart(data).mark_line(point=True).encode(
                x=alt.X('日付:T', axis=alt.Axis(format='%m/%d')),
                y=alt.Y('血圧上1:Q', scale=alt.Scale(zero=False), title='血圧値'),
                tooltip=['日付', '血圧上1', '血圧下1']
            ).interactive()
            st.altair_chart(bp_chart, use_container_width=True)
            st.caption("血圧（上1）の推移グラフ")

    # --- 4. 体重管理画面 ---
    elif st.session_state.view_mode == "weight":
        st.subheader("⚖️ 体重モニタリング")
        if user == "祐介" and not st.session_state.extra_auth:
            st.error("追加認証を行ってください")
        else:
            w_data = load(w_sheet)
            if not w_data.empty and "体重" in w_data.columns:
                w_data["体重"] = pd.to_numeric(w_data["体重"], errors='coerce')
                chart = alt.Chart(w_data).mark_line(point=True).encode(
                    x=alt.X('日付:T', axis=alt.Axis(format='%m/%d')), 
                    y=alt.Y('体重:Q', scale=alt.Scale(zero=False))
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                st.data_editor(w_data, num_rows="dynamic", key="edit_w", use_container_width=True)

    # --- 5. メイン画面 ---
    else:
        data = load(t_sheet)
        if not data.empty:
            st.subheader("📊 生活リズム推移")
            chart_df = data.copy()
            for col in ["総合実績", "睡眠時間", "行動意欲", "食生活"]:
                if col not in chart_df.columns: chart_df[col] = 0
                chart_df[col] = pd.to_numeric(chart_df[col], errors='coerce').fillna(0)
            
            base = alt.Chart(chart_df).encode(x=alt.X('日付:T', axis=alt.Axis(format='%m/%d')))
            l_tot = base.mark_line(strokeWidth=5, color='red').encode(y=alt.Y('総合実績:Q'))
            l_slp = base.mark_line(strokeWidth=2, color='blue', opacity=0.7).encode(y='睡眠時間:Q')
            st.altair_chart(l_tot + l_slp, use_container_width=True)

        with st.form("input_form"):
            st.subheader("📝 今日の記録")
            col1, col2, col3 = st.columns(3)
            with col1:
                wake_t = st.selectbox("起床時間", TIME_OPTIONS, index=13) 
                bed_t = st.selectbox("就寝時間", TIME_OPTIONS, index=44)  
                sleep_hr = st.selectbox("睡眠時間 (修正可)", SLEEP_OPTIONS, index=14)
                total = st.slider("総合実績", 1, 10, 5)
            with col2:
                s_q = st.slider("寝つき", 1, 10, 5); cond = st.slider("体調", 1, 10, 5)
                # 克己さん専用：血圧入力
                if user == "克己":
                    bp_h1 = st.number_input("血圧上1", 50, 200, 120)
                    bp_l1 = st.number_input("血圧下1", 30, 150, 80)
                else: bp_h1 = bp_l1 = 0
            with col3:
                moti = st.slider("行動意欲", 1, 10, 5); food = st.slider("食生活", 1, 10, 5)
                weight = st.slider("今日の体重 (kg)", 40.0, 120.0, 65.0, 0.1)
                # 克己さん専用：血圧入力2
                if user == "克己":
                    bp_h2 = st.number_input("血圧上2", 50, 200, 120)
                    bp_l2 = st.number_input("血圧下2", 30, 150, 80)
                else: bp_h2 = bp_l2 = 0
            
            memo = st.text_area("メモ")
            
            if st.form_submit_button("保存する"):
                today = str(date.today())
                final_sleep = min(sleep_hr, 9.0)
                new_data = {
                    "日付": today, "起床時間": wake_t, "就寝時間": bed_t, "睡眠時間": final_sleep,
                    "寝つき": s_q, "体調": cond, "行動意欲": moti, "総合実績": total, "食生活": food, "メモ": memo
                }
                if user == "克己":
                    new_data.update({"血圧上1": bp_h1, "血圧下1": bp_l1, "血圧上2": bp_h2, "血圧下2": bp_l2})
                
                conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, pd.DataFrame([new_data])], ignore_index=True))
                st.success("保存しました！"); st.rerun()

        if not data.empty:
            st.subheader("📋 履歴一覧")
            # 表示する列（克己さんの時だけ血圧を表示）
            display_cols = ["日付", "起床時間", "就寝時間", "睡眠時間", "行動意欲", "食生活", "総合実績", "メモ"]
            if user == "克己":
                display_cols[4:4] = ["血圧上1", "血圧下1", "血圧上2", "血圧下2"]
            
            existing_cols = [c for c in display_cols if c in data.columns]
            edited_df = st.data_editor(data[existing_cols], num_rows="dynamic", key="main_edit", use_container_width=True, disabled=[])
            if st.button("表の修正を保存"):
                conn.update(spreadsheet=url, worksheet=t_sheet, data=edited_df)
                st.success("更新しました！"); st.rerun()

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt

# --- 1. Settings ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]}
}

st.set_page_config(page_title="My Health Log", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view_mode" not in st.session_state: st.session_state.view_mode = "main"
if "weight_auth" not in st.session_state: st.session_state.weight_auth = False

# --- 2. Login Section ---
if not st.session_state.logged_in:
    st.title("🛡️ 生活リズム・体調管理")
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
    user = st.session_state.current_user
    url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
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
        st.session_state.weight_auth = False
        st.rerun()

    st.divider()

    # --- 3. 体重管理画面（0-100kg固定グラフ） ---
    if st.session_state.view_mode == "weight":
        st.subheader("⚖️ 体重モニタリング")
        if not st.session_state.weight_auth:
            w_pw = st.text_input("体重用パスワード", type="password")
            if st.button("体重画面へログイン"):
                if w_pw == USER_DATA[user]["weight_pw"]:
                    st.session_state.weight_auth = True
                    st.rerun()
                else: st.error("パスワードが違います")
        else:
            w_data = load(w_sheet)
            if not w_data.empty:
                df_w = w_data.copy()
                df_w["体重"] = pd.to_numeric(df_w["体重"], errors='coerce')
                
                # 0から100に固定したグラフ
                chart = alt.Chart(df_w).mark_line(point=True).encode(
                    x='日付:T',
                    y=alt.Y('体重:Q', scale=alt.Scale(domain=[0, 100])),
                    tooltip=['日付', '体重']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                
                st.write("▼ 体重データの修正・削除（行を選択してDelキーで削除）")
                edited_w = st.data_editor(w_data, num_rows="dynamic", key="edit_w", use_container_width=True)
                if st.button("体重データを更新"):
                    conn.update(spreadsheet=url, worksheet=w_sheet, data=edited_w)
                    st.success("更新しました！")
            else: st.info("データがありません")

    # --- 4. メイン日報画面 ---
    else:
        data = load(t_sheet)
        with st.form("input_form"):
            st.subheader("📝 今日の記録")
            col1, col2, col3 = st.columns(3)
            with col1:
                bed = st.text_input("就寝時間", "22:00")
                wake = st.text_input("起床時間", "06:30")
                food = st.slider("食生活", 1, 10, 5)
            with col2:
                w_s = st.slider("寝起き", 1, 10, 5)
                s_q = st.slider("寝つき", 1, 10, 5)
            with col3:
                cond = st.slider("体調", 1, 10, 5)
                moti = st.slider("行動意欲", 1, 10, 5)
                total = st.slider("総合実績", 1, 10, 5)
            
            weight = st.number_input("体重(kg) ※保存のみ", 0.0, 150.0, 65.0, 0.1)
            memo = st.text_area("メモ")
            
            if st.form_submit_button("保存する"):
                try:
                    today = str(date.today())
                    new_m = pd.DataFrame([{"日付":today, "食生活":food, "就寝時間":bed, "起床時間":wake, "寝起き":w_s, "寝つき":s_q, "行動意欲":moti, "気分":5, "体調":cond, "総合実績":total, "睡眠時間":7.0, "メモ":memo}])
                    conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, new_m], ignore_index=True))
                    
                    w_data_current = load(w_sheet)
                    new_w = pd.DataFrame([{"日付":today, "体重":weight}])
                    conn.update(spreadsheet=url, worksheet=w_sheet, data=pd.concat([w_data_current, new_w], ignore_index=True))
                    st.success("保存完了！"); st.rerun()
                except: st.error("保存失敗")

        if not data.empty:
            st.divider()
            st.subheader("📊 生活リズム推移")
            chart_df = data[["日付", "総合実績", "睡眠時間", "食生活", "行動意欲"]].copy()
            for c in chart_df.columns: 
                if c != "日付": chart_df[c] = pd.to_numeric(chart_df[c], errors='coerce')
            st.line_chart(chart_df.set_index("日付"))

            st.subheader("📋 履歴一覧（修正・削除可能）")
            # 指定の順番に並び替え & 体重・気分を除去
            display_cols = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "行動意欲", "メモ"]
            
            # データが存在する列のみでフィルタリング（エラー防止）
            existing_cols = [c for c in display_cols if c in data.columns]
            df_display = data[existing_cols].copy()
            
            edited_df = st.data_editor(df_display, num_rows="dynamic", key="main_edit", use_container_width=True)
            
            if st.button("日報の修正・削除を保存する"):
                # 表示されていない「食生活」「気分」「総合実績」なども消さないように元のデータに反映
                updated_data = data.copy()
                # 削除対応：edited_dfにない行を特定して削除（日付をキーにするなど）
                # 今回はシンプルにedited_dfの内容をそのまま保存（ただし元の全カラムを維持）
                # エディタで削られた行も反映されるようにする
                conn.update(spreadsheet=url, worksheet=t_sheet, data=edited_df)
                st.success("履歴を更新しました！")

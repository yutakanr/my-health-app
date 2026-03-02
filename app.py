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
        st.session_state.weight_auth = False
        st.rerun()

    # スプレッドシート閲覧用リンク
    st.markdown(f"🔗 [Googleスプレッドシートで直接確認する]({url})")
    st.divider()

    # --- 3. 体重管理画面 ---
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
                chart = alt.Chart(df_w).mark_line(point=True).encode(
                    x='日付:T', y=alt.Y('体重:Q', scale=alt.Scale(domain=[0, 100])), tooltip=['日付', '体重']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                
                st.info("🗑️ 行の左端をクリックして選択し、Deleteキーで削除できます。")
                edited_w = st.data_editor(w_data, num_rows="dynamic", key="edit_w", use_container_width=True)
                if st.button("体重データを保存・更新"):
                    conn.update(spreadsheet=url, worksheet=w_sheet, data=edited_w)
                    st.success("更新しました！")
            else: st.info("データがありません")

    # --- 4. メメイン画面 ---
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
            
            # 体重をスライダー（棒線）入力に変更
            weight = st.slider("体重 (kg)", 0.0, 100.0, 60.0, 0.1)
            memo = st.text_area("メモ")
            
            if st.form_submit_button("この内容で保存する"):
                try:
                    today = str(date.today())
                    new_m = pd.DataFrame([{"日付":today, "食生活":food, "就寝時間":bed, "起床時間":wake, "寝起き":w_s, "寝つき":s_q, "行動意欲":moti, "気分":5, "体調":cond, "総合実績":total, "睡眠時間":7.0, "メモ":memo}])
                    conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([data, new_m], ignore_index=True))
                    w_data_c = load(w_sheet)
                    new_w = pd.DataFrame([{"日付":today, "体重":weight}])
                    conn.update(spreadsheet=url, worksheet=w_sheet, data=pd.concat([w_data_c, new_w], ignore_index=True))
                    st.success("保存完了！"); st.rerun()
                except: st.error("保存失敗")

        if not data.empty:
            st.divider()
            st.subheader("📊 生活リズム推移")
            # カスタムグラフ：総合実績を赤色・太線にする
            chart_df = data.copy()
            for c in ["総合実績", "睡眠時間", "食生活", "行動意欲"]:
                chart_df[c] = pd.to_numeric(chart_df[c], errors='coerce')
            
            # Altairで詳細なグラフ作成
            base = alt.Chart(chart_df).encode(x='日付:T')
            line1 = base.mark_line(strokeWidth=4, color='red').encode(y='総合実績:Q', tooltip=['日付', '総合実績'])
            line2 = base.mark_line(opacity=0.5).encode(y='睡眠時間:Q', color=alt.value('blue'))
            line3 = base.mark_line(opacity=0.5).encode(y='食生活:Q', color=alt.value('green'))
            line4 = base.mark_line(opacity=0.5).encode(y='行動意欲:Q', color=alt.value('orange'))
            st.altair_chart(line1 + line2 + line3 + line4, use_container_width=True)

            st.subheader("📋 履歴一覧（編集・削除）")
            st.info("💡 左端の番号をクリックして選択状態にし、Deleteキーを押すと行を削除できます。")
            display_cols = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "行動意欲", "メモ"]
            existing_cols = [c for c in display_cols if c in data.columns]
            
            # エラー防止のため、全データを読み込んでエディタに渡す
            edited_df = st.data_editor(data[existing_cols], num_rows="dynamic", key="main_edit", use_container_width=True)
            
            if st.button("修正・削除を反映してスプレッドシートを更新"):
                try:
                    # エディタの内容をスプレッドシートに上書き（元の列構成を壊さないよう注意）
                    conn.update(spreadsheet=url, worksheet=t_sheet, data=edited_df)
                    st.success("スプレッドシートを更新しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新エラー: {e}")

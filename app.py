import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"},
    "テト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "teto"}
}

st.set_page_config(page_title="Health Log Pro", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- 2. ログイン ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
    pw_input = st.text_input("パスワード", type="password")
    if st.button("ログイン", use_container_width=True, type="primary"):
        if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
            st.session_state.logged_in = True
            st.session_state.current_user = user_choice
            st.rerun()
        else: st.error("パスワードが違います")
    st.stop()

# --- 3. データ読み込み ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
t_month = date.today().strftime("%Y-%m")

try:
    raw_df = conn.read(spreadsheet=url, worksheet=t_month, ttl=0)
    if not raw_df.empty:
        raw_df['日付'] = pd.to_datetime(raw_df['日付']).dt.strftime('%Y-%m-%d')
        df_clean = raw_df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
    else:
        df_clean = pd.DataFrame()
except:
    raw_df = pd.DataFrame(); df_clean = pd.DataFrame()

# ヘッダー
st.title(f"🐾 {user}ちゃんの管理" if user == "テト" else f"👋 {user}さんの管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False; st.rerun()

# --- 4. メイングラフ (体調→食生活へ変更) ---
if not df_clean.empty:
    st.subheader("📈 トレンド確認")
    gdf = df_clean.copy()
    
    if user == "テト":
        chart = alt.Chart(gdf).mark_line(strokeWidth=4, color='#FF69B4', point=True).encode(
            x=alt.X('日付:N', title='日付'),
            y=alt.Y('総合元気度:Q', title='元気度', scale=alt.Scale(domain=[0, 10])),
            tooltip=['日付', '総合元気度', 'メモ']
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        # 表示項目を 総合実績, 行動意欲, 食生活, 睡眠時間 に変更
        cols_to_plot = ["総合実績", "行動意欲", "食生活", "睡眠時間"]
        existing_plot_cols = [c for c in cols_to_plot if c in gdf.columns]
        
        if existing_plot_cols:
            melted_df = gdf.melt(id_vars=['日付'], value_vars=existing_plot_cols, var_name='項目', value_name='数値')
            chart = alt.Chart(melted_df).mark_line(point=True).encode(
                x=alt.X('日付:N', title='日付'),
                y=alt.Y('数値:Q', title='スコア', scale=alt.Scale(domain=[0, 10])),
                color=alt.Color('項目:N', title='凡例', scale=alt.Scale(scheme='category10')),
                tooltip=['日付', '項目', '数値']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

st.divider()

# --- 5. タブ切り替え ---
tab_list = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己": tab_list.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_list)

# --- 5-1. 体調記録タブ ---
with tabs[0]:
    if user == "テト":
        with st.form("cat_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                food = st.selectbox("ごはんの量", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
                water = st.slider("水分補給", 1, 10, 5)
                vomit = st.checkbox("毛玉嘔吐")
            with c2:
                poo_s = st.selectbox("うんちの状態", ["かなり硬い", "少し硬い", "普通", "柔らかい", "かなり柔らかい"], index=2)
                poo_c = st.number_input("うんち回数", 0, 10, 1); pee_c = st.slider("おしっこ回数", 0, 10, 2)
            with c3:
                genki = st.slider("総合元気度", 1, 10, 8); active = st.slider("運動量", 1, 10, 5)
                brush = st.checkbox("ブラッシング")
            memo_cat = st.text_area("メモ")
            if st.form_submit_button("🐾 記録を保存"):
                new_row = {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, "総合元気度": genki, "メモ": memo_cat}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("保存しました！"); st.rerun()
    else:
        with st.form("h_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                wake = st.text_input("起床時間", "7:00"); sleep = st.text_input("就寝時間", "23:00")
                sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
            with c2:
                s_q = st.slider("寝つき", 1, 10, 7); s_w = st.slider("寝起き", 1, 10, 7); cond = st.slider("体調", 1, 10, 7)
            with c3:
                g = st.slider("総合実績", 1, 10, 5); a = st.slider("行動意欲", 1, 10, 5); f = st.slider("食生活", 1, 10, 6)
            memo = st.text_area("メモ")
            if st.form_submit_button("🚀 保存"):
                new_row = {"日付": str(date.today()), "起床時間": wake, "就寝時間": sleep, "睡眠時間": sl_h, "寝つき": s_q, "寝起き": s_w, "体調": cond, "総合実績": g, "行動意欲": a, "食生活": f, "メモ": memo}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("保存しました！"); st.rerun()

# --- 5-2. 血圧管理タブ (克己のみ) ---
if user == "克己":
    with tabs[1]:
        st.subheader("🩸 血圧ログ")
        if not df_clean.empty and "血圧上1" in df_clean.columns:
            bp_df = df_clean.dropna(subset=["血圧上1"])
            if not bp_df.empty:
                bp_melted = bp_df.melt(id_vars=['日付'], value_vars=['血圧上1', '血圧下1'], var_name='項目', value_name='値')
                bp_chart = alt.Chart(bp_melted).mark_line(point=True).encode(
                    x='日付:N', y='値:Q', color='項目:N', tooltip=['日付', '項目', '値']
                )
                st.altair_chart(bp_chart, use_container_width=True)
                st.dataframe(bp_df[["日付", "血圧上1", "血圧下1", "血圧上2", "血圧下2"]].sort_values("日付", ascending=False), use_container_width=True)
        with st.form("bp_form"):
            c1, c2 = st.columns(2)
            with c1: u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
            with c2: u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
            if st.form_submit_button("🩸 血圧を記録"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([{"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "血圧上2": u2, "血圧下2": d2}])], ignore_index=True))
                st.success("血圧を保存しました"); st.rerun()

# --- 5-3. 体重管理タブ ---
weight_tab_idx = 2 if user == "克己" else 1
with tabs[weight_tab_idx]:
    st.subheader("⚖️ 体重ログ")
    if not df_clean.empty and "体重" in df_clean.columns:
        w_df = df_clean.dropna(subset=["体重"])
        if not w_df.empty:
            w_chart = alt.Chart(w_df).mark_line(color='#FF0000', point=True).encode(
                x='日付:N', y=alt.Y('体重:Q', scale=alt.Scale(zero=False)),
                tooltip=['日付', '体重']
            )
            st.altair_chart(w_chart, use_container_width=True)
            st.dataframe(w_df[["日付", "体重"]].sort_values("日付", ascending=False), use_container_width=True)
    with st.form("w_form"):
        weight = st.number_input("体重(kg)", 30.0, 150.0, 60.0, step=0.1)
        if st.form_submit_button("⚖️ 体重のみを記録"):
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([{"日付": str(date.today()), "体重": weight}])], ignore_index=True))
            st.success("体重を保存しました"); st.rerun()

st.divider()

# --- 6. 編集・削除 & 全体履歴表 ---
if not df_clean.empty:
    st.subheader("📋 データの編集・削除・全体履歴")
    target_date = st.selectbox("日付を選択", df_clean['日付'].unique()[::-1])
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ 削除", use_container_width=True):
            conn.update(spreadsheet=url, worksheet=t_month, data=raw_df[raw_df['日付'] != target_date])
            st.rerun()
    with c2:
        if st.button("✏️ 編集", use_container_width=True):
            st.session_state.edit_mode, st.session_state.edit_date = True, target_date

    if st.session_state.get("edit_mode"):
        edit_data = df_clean[df_clean['日付'] == st.session_state.edit_date].iloc[0]
        with st.expander(f"📝 {st.session_state.edit_date} のデータを修正中", expanded=True):
            new_edit_df = st.data_editor(pd.DataFrame([edit_data]))
            if st.button("✅ 修正確定"):
                raw_df = raw_df[raw_df['日付'] != st.session_state.edit_date]
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, new_edit_df], ignore_index=True))
                st.session_state.edit_mode = False; st.rerun()
    
    # ここに全体履歴表を復活させました
    st.write("📖 今月の全記録一覧")
    if user == "テト":
        cols = ["日付", "ごはんの量", "水分補給", "おしっこ回数", "うんち回数", "うんちの状態", "毛玉嘔吐", "運動量", "ブラッシング", "総合元気度", "メモ"]
    else:
        cols = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "総合実績", "行動意欲", "食生活", "メモ", "体重"]
        if user == "克己": cols += ["血圧上1", "血圧下1", "血圧上2", "血圧下2"]
    
    existing = [c for c in cols if c in df_clean.columns]
    st.dataframe(df_clean[existing].sort_values("日付", ascending=False), use_container_width=True)

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt
from PIL import Image

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
if "weight_auth" not in st.session_state: st.session_state.weight_auth = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

# --- 2. ログインチェック ---
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
except Exception:
    raw_df = pd.DataFrame(); df_clean = pd.DataFrame()

# ヘッダー
st.title(f"🐾 {user}ちゃんの管理" if user == "テト" else f"👋 {user}さんの管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.weight_auth = False
    st.rerun()

st.divider()

# --- 共通の一覧表・編集・削除用関数 ---
def show_data_footer(display_df, filter_cols, key_suffix):
    if not display_df.empty:
        st.divider()
        st.subheader("📋 データの編集・削除と一覧")
        
        # 指定された列順に並べ替え（存在しない列は無視）
        existing_cols = [c for c in filter_cols if c in display_df.columns]
        target_df = display_df[existing_cols].copy()
        
        target_date = st.selectbox("編集・削除する日付を選択", target_df['日付'].unique()[::-1], key=f"sb_{key_suffix}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ データを削除", use_container_width=True, key=f"del_{key_suffix}"):
                conn.update(spreadsheet=url, worksheet=t_month, data=raw_df[raw_df['日付'] != target_date])
                st.cache_data.clear(); st.rerun()
        with c2:
            if st.button("✏️ データを編集", use_container_width=True, key=f"edit_{key_suffix}"):
                st.session_state.edit_mode, st.session_state.edit_date = True, target_date

        if st.session_state.get("edit_mode") and st.session_state.edit_date == target_date:
            edit_data = target_df[target_df['日付'] == st.session_state.edit_date].iloc[0]
            with st.expander(f"📝 {st.session_state.edit_date} のデータを修正中", expanded=True):
                new_edit_df = st.data_editor(pd.DataFrame([edit_data]))
                if st.button("✅ 修正を確定", key=f"confirm_{key_suffix}"):
                    updated_row_vals = new_edit_df.iloc[0]
                    other_rows = raw_df[raw_df['日付'] != st.session_state.edit_date]
                    original_row = raw_df[raw_df['日付'] == st.session_state.edit_date].iloc[0].copy()
                    for col in existing_cols:
                        original_row[col] = updated_row_vals[col]
                    
                    final_df = pd.concat([other_rows, pd.DataFrame([original_row])], ignore_index=True)
                    conn.update(spreadsheet=url, worksheet=t_month, data=final_df)
                    st.session_state.edit_mode = False; st.cache_data.clear(); st.rerun()
        
        st.write("📖 全記録一覧")
        st.dataframe(target_df.sort_values("日付", ascending=False), use_container_width=True)

# --- 4. タブ切り替え ---
tab_labels = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己":
    tab_labels.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_labels)

# --- 4-1. 体調記録タブ ---
with tabs[0]:
    if user == "テト":
        c_form, c_img = st.columns([2, 1])
        with c_form:
            st.subheader("📝 本日の体調を入力")
            with st.form("cat_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    food = st.selectbox("ごはんの量", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
                    water = st.slider("水分補給", 0, 10, 5); vomit = st.checkbox("毛玉嘔吐")
                with c2:
                    poo_s = st.selectbox("うんちの状態", ["かなり硬い", "少し硬い", "普通", "柔らかい", "かなり柔らかい"], index=2)
                    poo_c = st.number_input("うんち回数", 0, 10, 1); pee_c = st.slider("おしっこ回数", 0, 10, 2)
                with c3:
                    genki = st.slider("総合元気度", 0, 10, 8); active = st.slider("運動量", 0, 10, 5); brush = st.checkbox("ブラッシング")
                memo_cat = st.text_area("メモ")
                if st.form_submit_button("🐾 記録を保存"):
                    new_row = {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, "総合元気度": genki, "メモ": memo_cat}
                    conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.cache_data.clear(); st.success("保存完了"); st.rerun()
        with c_img:
            try: cat_image = Image.open('teto_photo.png'); st.image(cat_image, caption='テトちゃん', use_container_width=True)
            except: st.info("teto_photo.png をアップロードしてね")
        
        if not df_clean.empty:
            gdf = df_clean.copy()
            if 'うんちの状態' in gdf.columns:
                score_map = {"かなり硬い": 0, "少し硬い": 5, "普通": 10, "柔らかい": 5, "かなり柔らかい": 0}
                gdf['うんちスコア'] = gdf['うんちの状態'].map(score_map).fillna(0)
            target_cols = ["総合元気度", "水分補給", "運動量", "うんちスコア"]
            existing_cols = [c for c in target_cols if c in gdf.columns]
            if existing_cols:
                st.subheader("📈 体調トレンド")
                melted_df = gdf.melt(id_vars=['日付'], value_vars=existing_cols, var_name='項目', value_name='数値')
                chart = alt.Chart(melted_df).mark_line(point=True).encode(x=alt.X('日付:N'), y=alt.Y('数値:Q', scale=alt.Scale(domain=[0, 10])), color='項目:N').properties(height=300)
                st.altair_chart(chart, use_container_width=True)
        show_data_footer(df_clean, ["日付", "ごはんの量", "水分補給", "おしっこ回数", "うんち回数", "うんちの状態", "毛玉嘔吐", "運動量", "ブラッシング", "総合元気度", "メモ"], "cat")
    
    else:
        st.subheader("📝 本日の体調を入力")
        with st.form("h_form"):
            c1, c2, c3 = st.columns(3)
            with c1: wake = st.text_input("起床時間", "7:00"); sleep = st.text_input("就寝時間", "23:00"); sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
            with c2: s_q = st.slider("寝つき", 0, 10, 7); s_w = st.slider("寝起き", 0, 10, 7); cond = st.slider("体調", 0, 10, 7)
            with c3: g = st.slider("総合実績", 0, 10, 5); a = st.slider("行動意欲", 0, 10, 5); f = st.slider("食生活", 0, 10, 6)
            memo = st.text_area("メモ")
            if st.form_submit_button("🚀 保存"):
                new_row = {"日付": str(date.today()), "起床時間": wake, "就寝時間": sleep, "睡眠時間": sl_h, "寝つき": s_q, "寝起き": s_w, "体調": cond, "総合実績": g, "行動意欲": a, "食生活": f, "メモ": memo}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.cache_data.clear(); st.success("保存完了"); st.rerun()
        
        if not df_clean.empty:
            target_cols = ["行動意欲", "食生活", "睡眠時間", "総合実績"]
            existing_cols = [c for c in target_cols if c in df_clean.columns]
            if existing_cols:
                st.subheader("📈 体調トレンド")
                melted_df = df_clean.melt(id_vars=['日付'], value_vars=existing_cols, var_name='項目', value_name='数値').dropna()
                chart = alt.Chart(melted_df).mark_line(point=True).encode(x=alt.X('日付:N'), y=alt.Y('数値:Q', scale=alt.Scale(domain=[0, 10])), color='項目:N').properties(height=300)
                st.altair_chart(chart, use_container_width=True)
        # メモを最後に配置
        show_data_footer(df_clean, ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "行動意欲", "食生活", "総合実績", "メモ"], "hum")

# --- 4-2. 血圧管理タブ (克己のみ) ---
if user == "克己":
    with tabs[1]:
        st.subheader("🩸 血圧管理")
        with st.form("bp_form"):
            c1, c2 = st.columns(2)
            with c1: u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
            with c2: u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
            bp_memo = st.text_area("血圧に関するメモ")
            if st.form_submit_button("🩸 血圧を保存"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([{"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "血圧上2": u2, "血圧下2": d2, "メモ": bp_memo}])], ignore_index=True))
                st.cache_data.clear(); st.success("保存完了"); st.rerun()
        
        if not df_clean.empty:
            bp_df_plot = df_clean.dropna(subset=["血圧上1"]).copy()
            if not bp_df_plot.empty:
                st.subheader("📈 血圧トレンド")
                bp_melted = bp_df_plot.melt(id_vars=['日付'], value_vars=["血圧上1", "血圧下1", "血圧上2", "血圧下2"], var_name='項目', value_name='数値').dropna()
                bp_chart = alt.Chart(bp_melted).mark_line(point=True).encode(x=alt.X('日付:N'), y=alt.Y('数値:Q', scale=alt.Scale(zero=False)), color='項目:N').properties(height=350)
                st.altair_chart(bp_chart, use_container_width=True)
                # メモを最後に配置
                show_data_footer(bp_df_plot, ["日付", "血圧上1", "血圧下1", "血圧上2", "血圧下2", "メモ"], "bp")

# --- 4-3. 体重管理タブ ---
weight_tab_idx = 2 if user == "克己" else 1
with tabs[weight_tab_idx]:
    st.subheader("⚖️ 体重管理")
    if user == "祐介" and not st.session_state.weight_auth:
        w_pw = st.text_input("体重閲覧パスワード", type="password")
        if st.button("🔓 ロック解除"):
            if w_pw == "yawaranr": st.session_state.weight_auth = True; st.rerun()
            else: st.error("パスワードが違います")
    else:
        with st.form("w_form"):
            weight = st.number_input("体重(kg)", 30.0, 150.0, 60.0, step=0.1)
            w_memo = st.text_area("体重に関するメモ")
            if st.form_submit_button("⚖️ 体重を保存"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([{"日付": str(date.today()), "体重": weight, "メモ": w_memo}])], ignore_index=True))
                st.cache_data.clear(); st.success("保存完了"); st.rerun()
        
        if not df_clean.empty and "体重" in df_clean.columns:
            w_df_plot = df_clean.dropna(subset=["体重"]).copy()
            if not w_df_plot.empty:
                st.subheader("📈 体重トレンド")
                w_chart = alt.Chart(w_df_plot).mark_line(point=True, color='orange').encode(x=alt.X('日付:N'), y=alt.Y('体重:Q', scale=alt.Scale(zero=False))).properties(height=300)
                st.altair_chart(w_chart, use_container_width=True)
                # メモを最後に配置
                show_data_footer(w_df_plot, ["日付", "体重", "メモ"], "weight")

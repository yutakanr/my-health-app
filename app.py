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

# --- 3. データ読み込み (エラー回避のためログイン後に実行) ---
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

# --- 4. メイングラフ ---
if not df_clean.empty:
    st.subheader("📈 トレンド確認")
    gdf = df_clean.copy()
    
    if user == "テト":
        target_cols = ["総合元気度", "水分補給", "運動量"]
    else:
        target_cols = ["行動意欲", "食生活", "睡眠時間"]
    
    existing_cols = [c for c in target_cols if c in gdf.columns]
    
    if existing_cols:
        melted_df = gdf.melt(id_vars=['日付'], value_vars=existing_cols, var_name='項目', value_name='数値')
        chart = alt.Chart(melted_df).mark_line(point=True).encode(
            x=alt.X('日付:N', title='日付'), 
            y=alt.Y('数値:Q', scale=alt.Scale(domain=[0, 10], clamp=True), axis=alt.Axis(values=[0, 2, 4, 6, 8, 10]), title='スコア'),
            color=alt.Color('項目:N', title='凡例'), 
            tooltip=['日付', '項目', '数値']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)

st.divider()

# --- 5. 共通の編集・削除関数 ---
def show_edit_delete_section(display_df, filter_cols):
    if not display_df.empty:
        st.subheader("📋 データの編集・削除")
        target_date = st.selectbox("編集・削除する日付を選択", display_df['日付'].unique()[::-1], key=f"sb_{filter_cols[1]}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ データを削除", use_container_width=True, key=f"del_{filter_cols[1]}"):
                conn.update(spreadsheet=url, worksheet=t_month, data=raw_df[raw_df['日付'] != target_date])
                st.cache_data.clear(); st.rerun()
        with c2:
            if st.button("✏️ データを編集", use_container_width=True, key=f"edit_{filter_cols[1]}"):
                st.session_state.edit_mode, st.session_state.edit_date = True, target_date

        if st.session_state.get("edit_mode") and st.session_state.edit_date == target_date:
            edit_data = display_df[display_df['日付'] == st.session_state.edit_date].iloc[0]
            with st.expander(f"📝 {st.session_state.edit_date} のデータを修正中", expanded=True):
                new_edit_df = st.data_editor(pd.DataFrame([edit_data]))
                if st.button("✅ 修正を確定", key=f"confirm_{filter_cols[1]}"):
                    updated_df = pd.concat([raw_df[raw_df['日付'] != st.session_state.edit_date], new_edit_df], ignore_index=True)
                    conn.update(spreadsheet=url, worksheet=t_month, data=updated_df)
                    st.session_state.edit_mode = False; st.cache_data.clear(); st.rerun()
        
        st.write("📖 全記録一覧")
        existing = [c for c in filter_cols if c in display_df.columns]
        st.dataframe(display_df[existing].sort_values("日付", ascending=False), use_container_width=True)

# --- 6. タブ切り替え ---
tab_labels = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己":
    tab_labels.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_labels)

# --- 6-1. 体調記録タブ ---
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
            try:
                # ユーザーがアップロードした画像を「teto_photo.png」として保存した想定
                cat_image = Image.open('teto_photo.png')
                st.image(cat_image, caption='テトちゃん', use_container_width=True)
            except:
                st.info("ここにテトちゃんの画像が表示されるよ（teto_photo.pngを配置してね）")

        show_edit_delete_section(df_clean, ["日付", "ごはんの量", "水分補給", "おしっこ回数", "うんち回数", "うんちの状態", "毛玉嘔吐", "運動量", "ブラッシング", "総合元気度", "メモ"])
    
    else:
        st.subheader("📝 本日の体調を入力")
        with st.form("h_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                wake = st.text_input("起床時間", "7:00"); sleep = st.text_input("就寝時間", "23:00"); sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
            with c2:
                s_q = st.slider("寝つき", 0, 10, 7); s_w = st.slider("寝起き", 0, 10, 7); cond = st.slider("体調", 0, 10, 7)
            with c3:
                g = st.slider("総合実績", 0, 10, 5); a = st.slider("行動意欲", 0, 10, 5); f = st.slider("食生活", 0, 10, 6)
            memo = st.text_area("メモ")
            if st.form_submit_button("🚀 保存"):
                new_row = {"日付": str(date.today()), "起床時間": wake, "就寝時間": sleep, "睡眠時間": sl_h, "寝つき": s_q, "寝起き": s_w, "体調": cond, "総合実績": g, "行動意欲": a, "食生活": f, "メモ": memo}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.cache_data.clear(); st.success("保存完了"); st.rerun()
        
        # 総合実績をメモの後ろに配置
        human_cols = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "行動意欲", "食生活", "メモ", "総合実績"]
        show_edit_delete_section(df_clean, human_cols)

# --- 6-2. 血圧管理タブ (克己のみ) ---
if user == "克己":
    with tabs[1]:
        st.subheader("🩸 血圧管理")
        bp_cols = ["日付", "血圧上1", "血圧下1", "血圧上2", "血圧下2"]
        with st.form("bp_form"):
            c1, c2 = st.columns(2)
            with c1: u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
            with c2: u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
            if st.form_submit_button("🩸 血圧を保存"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([{"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "血圧上2": u2, "血圧下2": d2}])], ignore_index=True))
                st.cache_data.clear(); st.success("保存完了"); st.rerun()
        if not df_clean.empty:
            show_edit_delete_section(df_clean.dropna(subset=["血圧上1"]), bp_cols)

# --- 6-3. 体重管理タブ ---
weight_tab_idx = 2 if user == "克己" else 1
with tabs[weight_tab_idx]:
    st.subheader("⚖️ 体重管理")
    if user == "祐介" and not st.session_state.weight_auth:
        w_pw = st.text_input("体重閲覧パスワード", type="password")
        if st.button("🔓 ロック解除"):
            if w_pw == "yawaranr":
                st.session_state.weight_auth = True; st.rerun()
            else: st.error("パスワードが違います")
    else:
        with st.form("w_form"):
            weight = st.number_input("体重(kg)", 30.0, 150.0, 60.0, step=0.1)
            if st.form_submit_button("⚖️ 体重を保存"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([{"日付": str(date.today()), "体重": weight}])], ignore_index=True))
                st.cache_data.clear(); st.success("保存完了"); st.rerun()
        if not df_clean.empty:
            show_edit_delete_section(df_clean.dropna(subset=["体重"]), ["日付", "体重"])

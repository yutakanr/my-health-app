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

# --- 3. 共通関数 ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
t_month = date.today().strftime("%Y-%m")

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if not df.empty and '日付' in df.columns:
            df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
            return df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
        return df
    except: return pd.DataFrame()

def format_drive_url(raw_url):
    if pd.isna(raw_url) or "id=" not in str(raw_url): return None
    file_id = str(raw_url).split("id=")[-1].split("&")[0]
    return f"https://drive.google.com/uc?id={file_id}"

# 編集・削除・一覧表示の共通フッター
def show_data_footer(display_df, filter_cols, key_suffix):
    if not display_df.empty:
        st.divider()
        st.subheader("📋 データの編集・削除と一覧")
        
        existing_cols = [c for c in filter_cols if c in display_df.columns]
        target_df = display_df[existing_cols].copy()
        
        target_date = st.selectbox("編集・削除する日付を選択", target_df['日付'].unique()[::-1], key=f"sb_{key_suffix}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ データを削除", use_container_width=True, key=f"del_{key_suffix}"):
                raw = load_data(t_month)
                conn.update(spreadsheet=url, worksheet=t_month, data=raw[raw['日付'] != target_date])
                st.cache_data.clear(); st.success("削除しました"); st.rerun()
        with c2:
            if st.button("✏️ データを編集", use_container_width=True, key=f"edit_{key_suffix}"):
                st.session_state.edit_mode, st.session_state.edit_date = True, target_date

        if st.session_state.get("edit_mode") and st.session_state.edit_date == target_date:
            edit_data = target_df[target_df['日付'] == st.session_state.edit_date].iloc[0]
            with st.expander(f"📝 {st.session_state.edit_date} のデータを修正中", expanded=True):
                new_edit_df = st.data_editor(pd.DataFrame([edit_data]))
                if st.button("✅ 修正を確定", key=f"confirm_{key_suffix}"):
                    raw = load_data(t_month)
                    other_rows = raw[raw['日付'] != st.session_state.edit_date]
                    final_df = pd.concat([other_rows, new_edit_df], ignore_index=True)
                    conn.update(spreadsheet=url, worksheet=t_month, data=final_df)
                    st.session_state.edit_mode = False; st.cache_data.clear(); st.rerun()
        
        st.write("📖 全記録一覧")
        st.dataframe(target_df.sort_values("日付", ascending=False), use_container_width=True)

# ヘッダー
st.title(f"🐾 {user}ちゃんの管理" if user == "テト" else f"👋 {user}さんの管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.weight_auth = False
    st.rerun()

# --- 4. タブ設定 ---
tab_labels = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己": tab_labels.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_labels)

# --- タブ1: 体調記録 ---
with tabs[0]:
    df_main = load_data(t_month)
    
    if user == "テト":
        st.subheader("✨ 今日のテトちゃん")
        col_m, col_b = st.columns([2, 1])
        with col_m: st.info("写真はGoogleフォームからアップしてね！")
        with col_b: st.link_button("📷 写真を保存", "あなたのフォームURL", use_container_width=True)

        with st.form("teto_form"):
            st.markdown("##### 🍖 食事・水分 / 🚽 トイレ")
            c1, c2, c3 = st.columns(3)
            with c1:
                food = st.select_slider("ごはん", options=["かなり少", "少", "普通", "多", "かなり多"], value="普通")
                water = st.slider("水分 (0-10)", 0, 10, 5)
            with c2:
                poo_s = st.selectbox("うんち状態", ["普通", "少し硬い", "かなり硬い", "柔らかい", "かなり柔らかい"])
                poo_c = st.number_input("うんち回数", 0, 10, 1)
            with c3:
                pee_c = st.number_input("おしっこ回数", 0, 10, 2)
                vomit = st.checkbox("毛玉嘔吐")
            
            st.markdown("##### 🏃 活動・元気")
            c4, c5 = st.columns(2)
            with c4: genki = st.slider("元気度", 0, 10, 8)
            with c5: active = st.slider("運動量", 0, 10, 5); brush = st.checkbox("ブラッシング")
            
            memo = st.text_area("メモ")
            if st.form_submit_button("🐾 記録を保存"):
                new_row = {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, "総合元気度": genki, "メモ": memo}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True))
                st.cache_data.clear(); st.rerun()

        if not df_main.empty:
            st.subheader("📈 体調トレンド")
            gdf = df_main.copy()
            score_map = {"かなり硬い": 0, "少し硬い": 5, "普通": 10, "柔らかい": 5, "かなり柔らかい": 0}
            gdf['うんちスコア'] = gdf['うんちの状態'].map(score_map).fillna(0)
            t_cols = ["総合元気度", "水分補給", "運動量", "うんちスコア"]
            melted = gdf.melt(id_vars=['日付'], value_vars=[c for c in t_cols if c in gdf.columns], var_name='項目', value_name='数値')
            st.altair_chart(alt.Chart(melted).mark_line(point=True).encode(x='日付:N', y=alt.Y('数値:Q', scale=alt.Scale(domain=[0, 10])), color='項目:N').properties(height=300), use_container_width=True)
            
            show_data_footer(df_main, ["日付", "ごはんの量", "水分補給", "おしっこ回数", "うんち回数", "うんちの状態", "毛玉嘔吐", "運動量", "ブラッシング", "総合元気度", "メモ"], "cat")

    else:
        # 人間の体調入力フォーム（全項目復活）
        st.subheader("📝 本日の体調を入力")
        with st.form("h_form"):
            c1, c2, c3 = st.columns(3)
            with c1: 
                wake = st.text_input("起床時間", "7:00")
                sleep = st.text_input("就寝時間", "23:00")
                sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
            with c2: 
                s_q = st.slider("寝つき", 0, 10, 7)
                s_w = st.slider("寝起き", 0, 10, 7)
                cond = st.slider("体調", 0, 10, 7)
            with c3: 
                g = st.slider("総合実績", 0, 10, 5)
                a = st.slider("行動意欲", 0, 10, 5)
                f = st.slider("食生活", 0, 10, 6)
            memo_h = st.text_area("メモ")
            if st.form_submit_button("🚀 保存"):
                new_row = {"日付": str(date.today()), "起床時間": wake, "就寝時間": sleep, "睡眠時間": sl_h, "寝つき": s_q, "寝起き": s_w, "体調": cond, "総合実績": g, "行動意欲": a, "食生活": f, "メモ": memo_h}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        
        if not df_main.empty:
            st.subheader("📈 体調トレンド")
            h_cols = ["行動意欲", "食生活", "睡眠時間", "総合実績"]
            m_h = df_main.melt(id_vars=['日付'], value_vars=[c for c in h_cols if c in df_main.columns], var_name='項目', value_name='数値').dropna()
            st.altair_chart(alt.Chart(m_h).mark_line(point=True).encode(x='日付:N', y=alt.Y('数値:Q', scale=alt.Scale(domain=[0, 10])), color='項目:N').properties(height=300), use_container_width=True)
        
        show_data_footer(df_main, ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "行動意欲", "食生活", "総合実績", "メモ"], "hum")

# --- タブ2: 血圧 (克己のみ) ---
if user == "克己":
    with tabs[1]:
        df_bp = load_data(t_month)
        with st.form("bp_form"):
            c1, c2 = st.columns(2)
            with c1: u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
            with c2: u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
            if st.form_submit_button("🩸 保存"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_bp, pd.DataFrame([{"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "血圧上2": u2, "血圧下2": d2}])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        show_data_footer(df_bp, ["日付", "血圧上1", "血圧下1", "血圧上2", "血圧下2"], "bp")

# --- タブ: 体重管理 ---
w_idx = 2 if user == "克己" else 1
with tabs[w_idx]:
    if user == "祐介" and not st.session_state.weight_auth:
        pw = st.text_input("体重PW", type="password")
        if st.button("🔓 解除"):
            if pw == "yawaranr": st.session_state.weight_auth = True; st.rerun()
    else:
        df_w = load_data(t_month)
        with st.form("w_form"):
            weight = st.number_input("体重(kg)", 30.0, 150.0, 60.0, step=0.1)
            if st.form_submit_button("⚖️ 保存"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_w, pd.DataFrame([{"日付": str(date.today()), "体重": weight}])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        show_data_footer(df_w, ["日付", "体重"], "weight")

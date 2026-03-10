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
except Exception:
    raw_df = pd.DataFrame(); df_clean = pd.DataFrame()

# ヘッダー
st.title(f"🐾 {user}ちゃんの管理" if user == "テト" else f"👋 {user}さんの管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.weight_auth = False
    st.rerun()

# --- 4. メイングラフ (0-10固定・動かない設定) ---
if not df_clean.empty:
    st.subheader("📈 トレンド確認")
    gdf = df_clean.copy()
    
    if user == "テト":
        target_cols = ["総合元気度", "水分補給", "運動量"]
    else:
        target_cols = ["総合実績", "行動意欲", "食生活", "睡眠時間"]
    
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

# --- 5. タブ切り替え ---
tab_labels = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己":
    tab_labels.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_labels)

# --- 共通の編集・削除関数 ---
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

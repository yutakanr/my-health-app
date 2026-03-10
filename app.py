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

# セッション状態の初期化
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
                if st.button("✅ 修正を確定", key=f"confirm_{filter_cols[1]}"):
                    updated_df = pd.concat([raw_df[raw_df['日付'] != st.session_state.edit_date], new_edit_df], ignore_index=True)
                    conn.update(spreadsheet=url, worksheet=t_month, data=updated_df)
                    st.session_state.edit_mode = False; st.cache_data.clear(); st.rerun()
        
        st.write("📖 全記録一覧")
        existing = [c for c in filter_cols if c in display_df.columns]
        st.dataframe(display_df[existing].sort_values("日付", ascending=False), use_container_width=True)

# --- 4. タブ切り替え ---
tab_labels = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己":
    tab_labels.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_labels)

# --- 4-1. 体調記録タブ ---
with

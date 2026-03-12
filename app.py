import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt
import base64
from io import BytesIO
from PIL import Image

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"},
    "テト": {"id": "1gHZ51t9qMDip_Gk_EjPH14Vke4BhbQEuf2ukZC3MxkQ", "pw": "teto"} 
}

st.set_page_config(page_title="Health Log Pro", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "weight_auth" not in st.session_state: st.session_state.weight_auth = False
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

# --- 画像変換用のヘルパー関数 (エラー耐性強化) ---
def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((400, 400)) # サイズを少し小さくして安定化
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=60)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception:
        return ""

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

# --- 3. 共通設定とデータ読み込み ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"

st.sidebar.header("🗓️ 表示設定")
today = date.today()
month_options = [(today.replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
selected_month = st.sidebar.selectbox("表示する月を選択", month_options)

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if df is not None and not df.empty:
            df = df.dropna(how='all')
            if '日付' in df.columns:
                df = df.dropna(subset=['日付'])
                df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
                return df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# 項目を消さずに保存する「マージ保存」関数
def save_entry(sheet_name, new_data_dict):
    existing_df = load_data(sheet_name)
    target_date = new_data_dict["日付"]
    
    if not existing_df.empty and target_date in existing_df["日付"].values:
        # 既存行を特定して、新しい値があるところだけ上書き
        idx = existing_df[existing_df["日付"] == target_date].index[0]
        for col, val in new_data_dict.items():
            if val is not None and val != "": # 空データで上書きしない
                existing_df.at[idx, col] = val
        final_df = existing_df
    else:
        # 新規行として追加
        final_df = pd.concat([existing_df, pd.DataFrame([new_data_dict])], ignore_index=True)
    
    # NaNを空文字に変換して保存（バグ防止）
    final_df = final_df.fillna("")
    conn.update(spreadsheet=url, worksheet=sheet_name, data=final_df)
    st.cache_data.clear()

# --- 4. 共通フッター ---
def show_data_footer(display_df, filter_cols, key_suffix):
    if not display_df.empty:
        st.divider()
        st.subheader(f"📋 {selected_month} のデータ詳細")
        
        target_date = st.selectbox("日付を選択", display_df['日付'].unique()[::-1], key=f"sb_{key_suffix}")
        selected_row = display_df[display_df['日付'] == target_date].iloc[0]
        
        if "画像URL" in selected_row and str(selected_row["画像URL"]).startswith("data:image"):
            st.image(selected_row["画像URL"], caption=f"{target_date} の写真", use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ 削除", use_container_width=True, key=f"del_{key_suffix}"):
                raw = load_data(selected_month)
                conn.update(spreadsheet=url, worksheet=selected_month, data=raw[raw['日付'] != target_date])
                st.cache_data.clear(); st.rerun()
        with c2:
            if st.button("✏️ 編集", use_container_width=True, key=f"edit_{key_suffix}"):
                st.session_state.edit_mode, st.session_state.edit_date = True, target_date

        if st.session_state.get("edit_mode") and st.session_state.edit_date == target_date:
            with st.expander("📝 編集実行中", expanded=True):
                current_cols = [c for c in filter_cols if c in display_df.columns]
                edit_df = st.data_editor(pd.DataFrame([selected_row[current_cols]]))
                if st.button("✅ 確定", key=f"confirm_{key_suffix}"):
                    save_entry(selected_month, edit_df.iloc[0].to_dict())
                    st.session_state.edit_mode = False; st.rerun()
        
        st.dataframe(display_df.sort_values("日付", ascending=False), use_

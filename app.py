import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import os

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

# --- 3. 共通設定 ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
# 今月のシート名 (例: 2026-03)
t_month = date.today().strftime("%Y-%m")

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if df is not None and not df.empty and '日付' in df.columns:
            df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 🚀 ヘッダー ---
st.title(f"🐾 {user}の体調管理")

# --- 4. タブ ---
tab_labels = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己": tab_labels.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_labels)

# --- テトの体調記録タブ ---
with tabs[0]:
    if user == "テト":
        with st.form("teto_form"):
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
            
            memo = st.text_area("メモ")
            
            if st.form_submit_button("🐾 記録を保存", use_container_width=True, type="primary"):
                try:
                    # 1. 保存するデータを作成
                    new_row = {
                        "日付": str(date.today()), 
                        "ごはんの量": food, 
                        "水分補給": water, 
                        "おしっこ回数": pee_c, 
                        "うんち回数": poo_c, 
                        "うんちの状態": poo_s, 
                        "毛玉嘔吐": vomit, 
                        "睡眠時間": 0,
                        "運動量": 5, 
                        "ブラッシング": False,
                        "写真名": "",
                        "総合元気度": 8, 
                        "メモ": memo
                    }
                    
                    # 2. 現在のデータを読み込む
                    current_df = load_data(t_month)
                    
                    # 3. データを合体
                    if current_df.empty:
                        updated_df = pd.DataFrame([new_row])
                    else:
                        updated_df = pd.concat([current_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    # 4. 書き込み実行
                    conn.update(spreadsheet=url, worksheet=t_month, data=updated_df)
                    st.cache_data.clear()
                    st.success("✅ スプレッドシートに保存しました！")
                except Exception as e:
                    st.error(f"保存に失敗したよ: {e}")

        # 下部に一覧表示
        df_display = load_data(t_month)
        if not df_display.empty:
            st.subheader("📋 過去の記録")
            st.dataframe(df_display.sort_values("日付", ascending=False), use_container_width=True)
    else:
        st.write("体調記録フォーム (作成中)")

# --- 体重管理タブ (テト以外も共通) ---
w_idx = 2 if user == "克己" else 1
with tabs[w_idx]:
    st.subheader("⚖️ 体重記録")
    # 体重の保存処理も同様に記述（今回はテト優先のため省略）

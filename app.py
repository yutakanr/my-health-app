import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"},
    "テト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "teto"}
}

st.set_page_config(page_title="Health Log Dual-Separate", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- 2. ログイン ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    with st.container(border=True):
        user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
        pw_input = st.text_input("パスワード", type="password")
        if st.button("ログイン", use_container_width=True, type="primary"):
            if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
                st.session_state.logged_in = True
                st.session_state.current_user = user_choice
                st.rerun()
            else: st.error("パスワードが違います")
    st.stop()

# --- 3. メイン設定 ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
t_month = date.today().strftime("%Y-%m")

# ヘッダー
st.title(f"🏥 {user}さんの管理パネル")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# 既存データの読み込み
try:
    df = conn.read(spreadsheet=url, worksheet=t_month, ttl=0)
except:
    df = pd.DataFrame()

# --- 4. タブ切り替え ---
tab_cat, tab_human = st.tabs(["🐾 テトちゃんの記録", "🚶 自分の記録"])

# --- 猫専用タブ ---
with tab_cat:
    st.subheader("🐱 テトちゃんの体調入力")
    with st.form("cat_input"):
        c1, c2, c3 = st.columns(3)
        with c1:
            food = st.selectbox("ごはんの量", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
            water = st.slider("水分補給", 1, 10, 5)
            vomit = st.checkbox("毛玉・嘔吐あり")
        with c2:
            poo_s = st.selectbox("うんちの状態", ["かなり硬い", "少し硬い", "普通", "柔らかい", "かなり柔らかい"], index=2)
            poo_c = st.number_input("うんち回数", 0, 10, 1)
            pee_c = st.slider("おしっこ回数", 0, 10, 2)
        with c3:
            genki = st.slider("総合元気度", 1, 10, 8)
            active = st.slider("運動量", 1, 10, 5)
            brush = st.checkbox("ブラッシング/ケア済")
        
        memo_cat = st.text_area("テトちゃんへのメモ")
        
        if st.form_submit_button("🐾 テトちゃんの記録を保存", type="primary"):
            new_row = {
                "日付": str(date.today()), "種別": "猫", "記録者": user,
                "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c,
                "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush,
                "総合元気度": genki, "メモ": memo_cat
            }
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("テトちゃんの記録を保存しました！")
            st.rerun()

# --- 人間専用タブ ---
with tab_human:
    st.subheader(f"🚶 {user}さんの体調入力")
    with st.form("human_input"):
        c1, c2 = st.columns(2)
        with c1:
            sleep = st.selectbox("睡眠状況", ["かなり寝た", "結構寝た", "普通に寝た", "あまり寝てない", "ほとんど寝てない"], index=2)
            h_genki = st.slider("総合実績", 1, 10, 5)
        with c2:
            h_active = st.slider("行動意欲", 1, 10, 5)
        
        memo_human = st.text_area("自分の日記・メモ")
        
        if st.form_submit_button("🚀 自分の記録を保存", type="primary"):
            new_row = {
                "日付": str(date.today()), "種別": "人間", "記録者": user,
                "睡眠時間": sleep, "総合実績": h_genki, "行動意欲": h_active, "メモ": memo_human
            }
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("自分の記録を保存しました！")
            st.rerun()

# --- 5. 履歴表示 ---
st.divider()
st.subheader("📋 履歴一覧")

if not df.empty:
    # フィルター（見やすくするために「猫だけ」「人間だけ」を選べるように）
    view_mode = st.radio("表示切り替え", ["すべて", "猫の記録のみ", "人間の記録のみ"], horizontal=True)
    
    display_df = df.copy()
    if view_mode == "猫の記録のみ":
        display_df = display_df[display_df["種別"] == "猫"]
    elif view_mode == "人間の記録のみ":
        display_df = display_df[display_df["種別"] == "人間"]
        
    st.dataframe(display_df.sort_values("日付", ascending=False), use_container_width=True)

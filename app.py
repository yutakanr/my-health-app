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

st.set_page_config(page_title="Health Log Dual", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- 2. ログイン ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    user_choice = st.selectbox("👤 ユーザー", ["選択してください"] + list(USER_DATA.keys()))
    pw_input = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
            st.session_state.logged_in = True
            st.session_state.current_user = user_choice
            st.rerun()
    st.stop()

# --- 3. メイン画面設定 ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
t_month = date.today().strftime("%Y-%m")

st.title(f"👋 {user}さんの管理パネル")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# タブで「猫」と「人間」を分ける
tab_cat, tab_human, tab_weight = st.tabs(["🐾 テトちゃんの記録", "🚶 自分の記録", "⚖️ 体重管理"])

# --- A. テトちゃんの記録タブ ---
with tab_cat:
    st.subheader("📝 テトちゃんの体調管理")
    try:
        df_cat = conn.read(spreadsheet=url, worksheet=t_month, ttl=0)
    except:
        df_cat = pd.DataFrame()

    with st.form("cat_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            food = st.selectbox("ごはん", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
            vomit = st.checkbox("嘔吐あり")
        with c2:
            poo = st.selectbox("うんち", ["かなり硬い", "少し硬い", "普通", "柔らかい", "かなり柔らかい"], index=2)
            pee = st.slider("おしっこ回数", 0, 10, 2)
        with c3:
            genki = st.slider("元気度", 1, 10, 8)
            memo_cat = st.text_area("メモ", placeholder="テトちゃんの様子")
        
        if st.form_submit_button("🐾 猫の記録を保存"):
            new_cat = {"日付": str(date.today()), "ごはんの量": food, "うんちの状態": poo, "おしっこ回数": pee, "毛玉嘔吐": vomit, "総合元気度": genki, "メモ": memo_cat}
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_cat, pd.DataFrame([new_cat])], ignore_index=True))
            st.success("テトちゃんの記録完了！")
            st.rerun()

# --- B. 人間の記録タブ ---
with tab_human:
    st.subheader("🏃 自分の体調管理")
    # 人間用のシート名が別にある場合はここを修正してください（例: "人間記録"など）
    # 今回は同じ月別シートに保存する前提で書きます
    with st.form("human_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            sleep = st.selectbox("睡眠状況", ["かなり寝た", "普通", "あまり寝てない"], index=1)
        with c2:
            h_genki = st.slider("総合実績", 1, 10, 5)
        with c3:
            h_active = st.slider("行動意欲", 1, 10, 5)
        
        h_memo = st.text_area("日記・メモ", placeholder="今日の自分の出来事")

        if st.form_submit_button("🚀 自分の記録を保存"):
            # 人間用は項目名を変えて保存
            new_human = {"日付": str(date.today()), "睡眠時間": sleep, "総合実績": h_genki, "行動意欲": h_active, "メモ": h_memo}
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_cat, pd.DataFrame([new_human])], ignore_index=True))
            st.success("自分の記録完了！")
            st.rerun()

# --- C. 履歴表示 ---
st.divider()
st.subheader("📋 履歴一覧")
if not df_cat.empty:
    st.dataframe(df_cat.sort_values("日付", ascending=False), use_container_width=True)

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
    df = conn.read(spreadsheet=url, worksheet=t_month, ttl=0)
except:
    df = pd.DataFrame()

# --- 4. ヘッダー ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title(f"🏥 {user}さんの管理パネル")
with col_h2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- 5. グラフセクション ---
if not df.empty:
    st.subheader("📈 直近のトレンド")
    gdf = df.copy()
    gdf['日付'] = pd.to_datetime(gdf['日付'])
    
    # 人間用と猫用でグラフを分ける、または統合して表示
    base = alt.Chart(gdf).encode(x=alt.X('日付:T', axis=alt.Axis(format='%m/%d')))
    
    # 総合実績 or 総合元気度をプロット
    lines = []
    if "総合実績" in gdf.columns:
        lines.append(base.mark_line(color='#1f77b4', strokeWidth=3).encode(y='総合実績:Q', tooltip=['日付', '総合実績']))
    if "総合元気度" in gdf.columns:
        lines.append(base.mark_line(color='#ff69b4', strokeWidth=3).encode(y='総合元気度:Q', tooltip=['日付', '総合元気度']))
    
    if lines:
        st.altair_chart(alt.layer(*lines), use_container_width=True)
        st.write("🔵 自分の実績  |  💗 テトちゃんの元気度")

st.divider()

# --- 6. 入力セクション（デフォルトタブの制御） ---
# テトでログインした時は猫タブ(0)、それ以外は人間タブ(1)をデフォルトに
default_tab = 0 if user == "テト" else 1
tab_cat, tab_human = st.tabs(["🐾 テトちゃんの記録", "🚶 自分の記録"])

# --- 猫タブ ---
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
            new_cat = {"日付": str(date.today()), "種別": "猫", "記録者": user, "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, "総合元気度": genki, "メモ": memo_cat}
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df, pd.DataFrame([new_cat])], ignore_index=True))
            st.success("保存完了！")
            st.rerun()

# --- 人間タブ ---
with tab_human:
    st.subheader(f"🚶 {user}さんの体調入力")
    with st.form("human_input"):
        c1, c2, c3 = st.columns(3)
        with c1:
            wake_t = st.text_input("起床時間", value="7:00")
            sleep_t = st.text_input("就寝時間", value="23:00")
            sleep_h = st.number_input("睡眠時間(h)", 0.0, 24.0, 7.0)
        with c2:
            s_quality = st.slider("寝つき", 1, 10, 7)
            s_wake = st.slider("寝起き", 1, 10, 7)
            condition = st.slider("体調", 1, 10, 7)
        with c3:
            h_genki = st.slider("総合実績", 1, 10, 5)
            h_active = st.slider("行動意欲", 1, 10, 5)
            h_food = st.slider("食生活", 1, 10, 6)
        
        memo_human = st.text_area("自分の日記・メモ")
        if st.form_submit_button("🚀 自分の記録を保存", type="primary"):
            new_human = {"日付": str(date.today()), "種別": "人間", "記録者": user, "起床時間": wake_t, "就寝時間": sleep_t, "睡眠時間": sleep_h, "寝つき": s_quality, "寝起き": s_wake, "体調": condition, "総合実績": h_genki, "行動意欲": h_active, "食生活": h_food, "メモ": memo_human}
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df, pd.DataFrame([new_human])], ignore_index=True))
            st.success("保存完了！")
            st.rerun()

# --- 7. 履歴表示 ---
if not df.empty:
    st.subheader("📋 履歴一覧")
    st.dataframe(df.sort_values("日付", ascending=False), use_container_width=True)

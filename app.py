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

# --- 3. データ読み込み & 重複排除 ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
t_month = date.today().strftime("%Y-%m")

try:
    df = conn.read(spreadsheet=url, worksheet=t_month, ttl=0)
    if not df.empty:
        # 日付でソートして、同じ日があれば「最後（最新）」を残す
        df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
        df = df.drop_duplicates(subset=['日付'], keep='last')
except:
    df = pd.DataFrame()

# ヘッダー
st.title(f"🐾 {user}ちゃんの健康管理" if user == "テト" else f"👋 {user}さんの健康管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. グラフセクション ---
if not df.empty:
    st.subheader("📈 体調トレンド")
    gdf = df.copy()
    gdf['日付'] = pd.to_datetime(gdf['日付'])
    base = alt.Chart(gdf).encode(x=alt.X('日付:T', axis=alt.Axis(format='%m/%d', title='日付')))

    if user == "テト":
        map_10 = {"かなり多い": 8, "多い": 6, "普通": 4, "少なめ": 2, "かなり少なめ": 0, "かなり柔らかい": 8, "柔らかい": 6, "少し硬い": 2, "かなり硬い": 0}
        if "ごはんの量" in gdf.columns: gdf['ごはん値'] = gdf['ごはんの量'].map(map_10).fillna(0)
        if "うんちの状態" in gdf.columns: gdf['うんち値'] = gdf['うんちの状態'].map(map_10).fillna(0)
        
        l1 = base.mark_line(strokeWidth=4, color='#FF69B4').encode(y=alt.Y('総合元気度:Q', scale=alt.Scale(domain=[0, 10])))
        l2 = base.mark_line(color='#32CD32').encode(y='ごはん値:Q')
        l3 = base.mark_line(color='#FFA500').encode(y='うんち値:Q')
        l4 = base.mark_line(color='#00BFFF').encode(y='運動量:Q')
        st.altair_chart(l1 + l2 + l3 + l4, use_container_width=True)
        st.write("💗元気度(太線)  💚ごはん  🧡うんち  💙運動量")
    else:
        # 人間用グラフ（1日ごとの最新値を反映）
        cols_map = {"総合実績": '#1f77b4', "行動意欲": '#ff7f0e', "体調": '#2ca02c', "睡眠時間": '#d62728'}
        lines = []
        for col, color in cols_map.items():
            if col in gdf.columns:
                gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)
                lines.append(base.mark_line(color=color, strokeWidth=3).encode(y=alt.Y(f'{col}:Q', scale=alt.Scale(domain=[0, 10]))))
        
        if lines:
            st.altair_chart(alt.layer(*lines), use_container_width=True)
            st.write("🔵総合実績  🟠行動意欲  🟢体調  🔴睡眠時間")

st.divider()

# --- 5. 入力セクション ---
if user == "テト":
    with st.form("cat_form"):
        st.subheader("🐱 テトちゃんの体調入力")
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
        memo_cat = st.text_area("メモ")
        if st.form_submit_button("🐾 記録を保存", type="primary"):
            new_row = {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, "総合元気度": genki, "メモ": memo_cat}
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("保存しました！"); st.rerun()
else:
    tab_list = ["🚶 自分の記録", "⚖️ 体重管理"]
    if user == "克己": tab_list.insert(1, "🩸 血圧管理")
    tabs = st.tabs(tab_list)
    
    with tabs[0]:
        with st.form("human_form"):
            st.subheader(f"🚶 {user}さんの体調入力")
            c1, c2, c3 = st.columns(3)
            with c1:
                wake_t = st.text_input("起床時間", value="7:00")
                sleep_t = st.text_input("就寝時間", value="23:00")
                sleep_h = st.number_input("睡眠時間(h)", 0.0, 24.0, 7.0) # st.number_inputに修正
            with c2:
                s_quality = st.slider("寝つき", 1, 10, 7)
                s_wake = st.slider("寝起き", 1, 10, 7)
                condition = st.slider("体調", 1, 10, 7)
            with c3:
                h_genki = st.slider("総合実績", 1, 10, 5)
                h_active = st.slider("行動意欲", 1, 10, 5)
                h_food = st.slider("食生活", 1, 10, 6)
            memo_h = st.text_area("自分の日記・メモ")
            if st.form_submit_button("🚀 自分の記録を保存", type="primary"):
                new_row = {"日付": str(date.today()), "起床時間": wake_t, "就寝時間": sleep_t, "睡眠時間": sleep_h, "寝つき": s_quality, "寝起き": s_wake, "体調": condition, "総合実績": h_genki, "行動意欲": h_active, "食生活": h_food, "メモ": memo_h}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("保存しました！"); st.rerun()

    if user == "克己":
        with tabs[1]:
            with st.form("bp_form"):
                st.subheader("🩸 血圧管理")
                col1, col2 = st.columns(2)
                with col1:
                    sys = st.number_input("最高血圧", 80, 200, 120)
                    dia = st.number_input("最低血圧", 40, 120, 80)
                with col2:
                    pulse = st.number_input("脈拍", 30, 150, 70)
                if st.form_submit_button("🩸 血圧を記録", type="primary"):
                    new_row = {"日付": str(date.today()), "最高血圧": sys, "最低血圧": dia, "脈拍": pulse}
                    conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                    st.success("血圧を保存しました！"); st.rerun()

# 履歴表示（ここでも重複排除後のデータを表示）
if not df.empty:
    st.subheader("📋 履歴一覧 (1日1最新データ)")
    st.dataframe(df.sort_values("日付", ascending=False), use_container_width=True)

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt

# --- 1. ユーザーデータ設定 (祐介さんを復元) ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yawaranr"},
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

# --- 3. データ読み込み & 1日1データ厳選 (グラフ重複防止) ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
t_month = date.today().strftime("%Y-%m")

try:
    raw_df = conn.read(spreadsheet=url, worksheet=t_month, ttl=0)
    if not raw_df.empty:
        # 日付を確実に統一
        raw_df['日付'] = pd.to_datetime(raw_df['日付']).dt.date
        # 【重要】同じ日付がある場合、最後の行（最新）だけを採用してグラフ用にする
        df_clean = raw_df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
    else:
        df_clean = pd.DataFrame()
except:
    raw_df = pd.DataFrame()
    df_clean = pd.DataFrame()

# ヘッダー
st.title(f"🐾 {user}ちゃんの健康管理" if user == "テト" else f"👋 {user}さんの健康管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. グラフセクション ---
if not df_clean.empty:
    st.subheader("📈 体調トレンド (1日1最新データ)")
    gdf = df_clean.copy()
    # X軸をOrdinal(:O)にすることで日付の重複表示を物理的に防ぐ
    base = alt.Chart(gdf).encode(x=alt.X('日付:O', axis=alt.Axis(labelAngle=0, title='日付')))

    if user == "テト":
        map_10 = {"かなり多い": 8, "多い": 6, "普通": 4, "少なめ": 2, "かなり少なめ": 0}
        if "ごはんの量" in gdf.columns: gdf['ごはん値'] = gdf['ごはんの量'].map(map_10).fillna(0)
        l1 = base.mark_line(strokeWidth=4, color='#FF69B4', point=True).encode(y=alt.Y('総合元気度:Q', scale=alt.Scale(domain=[0, 10])))
        st.altair_chart(l1, use_container_width=True)
    else:
        cols_map = {"総合実績": '#1f77b4', "行動意欲": '#ff7f0e', "体調": '#2ca02c', "睡眠時間": '#d62728'}
        lines = []
        for col, color in cols_map.items():
            if col in gdf.columns:
                gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)
                lines.append(base.mark_line(color=color, strokeWidth=3, point=True).encode(y=alt.Y(f'{col}:Q', scale=alt.Scale(domain=[0, 10]))))
        if lines: st.altair_chart(alt.layer(*lines), use_container_width=True)

st.divider()

# --- 5. 入力セクション ---
if user == "テト":
    with st.form("cat_form"):
        st.subheader("🐱 体調入力")
        c1, c2 = st.columns(2)
        with c1:
            food = st.selectbox("ごはんの量", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
            genki = st.slider("総合元気度", 1, 10, 8)
        with c2:
            poo_c = st.number_input("うんち回数", 0, 10, 1)
            active = st.slider("運動量", 1, 10, 5)
        if st.form_submit_button("🐾 記録を保存"):
            new_row = {"日付": str(date.today()), "ごはんの量": food, "うんち回数": poo_c, "運動量": active, "総合元気度": genki}
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("保存しました！"); st.rerun()
else:
    # 祐介さんと克己さんのタブ構成
    tab_titles = ["🚶 自分の記録", "⚖️ 体重管理"]
    if user == "克己": tab_titles.insert(1, "🩸 血圧管理")
    tabs = st.tabs(tab_titles)
    
    with tabs[0]:
        with st.form("human_form"):
            c1, c2 = st.columns(2)
            with c1:
                condition = st.slider("体調", 1, 10, 7)
                h_genki = st.slider("総合実績", 1, 10, 5)
            with c2:
                h_active = st.slider("行動意欲", 1, 10, 5)
                h_food = st.slider("食生活", 1, 10, 6)
            if st.form_submit_button("🚀 記録を保存"):
                new_row = {"日付": str(date.today()), "体調": condition, "総合実績": h_genki, "行動意欲": h_active, "食生活": h_food}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("保存しました！"); st.rerun()

    if user == "克己":
        with tabs[1]:
            st.subheader("🩸 血圧管理 (上1・下1・上2・下2)")
            with st.form("bp_form"):
                c1, c2 = st.columns(2)
                with c1:
                    u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
                with c2:
                    u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
                if st.form_submit_button("🩸 血圧を記録"):
                    new_row = {"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "血圧上2": u2, "血圧下2": d2}
                    conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.success("血圧を保存しました！"); st.rerun()

    # 体重管理タブ (祐介/克己/典子 共通)
    weight_idx = 2 if user == "克己" else 1
    with tabs[weight_idx]:
        st.subheader("⚖️ 体重管理")
        with st.form("weight_form"):
            weight = st.number_input("体重 (kg)", 30.0, 150.0, 60.0, step=0.1)
            if st.form_submit_button("⚖️ 体重を記録"):
                new_row = {"日付": str(date.today()), "体重": weight}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("体重を保存しました！"); st.rerun()

# 履歴表示 (最新順)
if not df_clean.empty:
    st.subheader("📋 履歴一覧 (最新データ)")
    st.dataframe(df_clean.sort_values("日付", ascending=False), use_container_width=True)

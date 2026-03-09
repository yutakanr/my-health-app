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

# --- 3. データ読み込み & 1日1データ厳選 ---
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
    base = alt.Chart(gdf).encode(x=alt.X('日付:N', title='日付', axis=alt.Axis(labelAngle=-45)))

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
        st.subheader("🐱 猫用・体調入力")
        c1, c2 = st.columns(2)
        with c1:
            food = st.selectbox("ごはんの量", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
            genki = st.slider("総合元気度", 1, 10, 8)
        with c2:
            poo_c = st.number_input("うんち回数", 0, 10, 1)
            active = st.slider("運動量", 1, 10, 5)
        memo_cat = st.text_area("様子メモ")
        if st.form_submit_button("🐾 記録を保存"):
            new_row = {"日付": str(date.today()), "ごはんの量": food, "うんち回数": poo_c, "運動量": active, "総合元気度": genki, "メモ": memo_cat}
            conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("保存しました！"); st.rerun()
else:
    tab_titles = ["🚶 自分の記録", "⚖️ 体重管理"]
    if user == "克己": tab_titles.insert(1, "🩸 血圧管理")
    tabs = st.tabs(tab_titles)
    
    with tabs[0]:
        with st.form("human_form"):
            c1, c2 = st.columns(2)
            with c1:
                sleep_h = st.number_input("睡眠時間(h)", 0.0, 24.0, 7.0)
                condition = st.slider("体調", 1, 10, 7)
            with c2:
                h_genki = st.slider("総合実績", 1, 10, 5)
                h_active = st.slider("行動意欲", 1, 10, 5)
            memo_h = st.text_area("日記・メモ")
            if st.form_submit_button("🚀 記録を保存"):
                new_row = {"日付": str(date.today()), "睡眠時間": sleep_h, "体調": condition, "総合実績": h_genki, "行動意欲": h_active, "メモ": memo_h}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("保存しました！"); st.rerun()

    if user == "克己":
        with tabs[1]:
            st.subheader("🩸 血圧管理")
            with st.form("bp_form"):
                u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
                u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
                if st.form_submit_button("🩸 記録"):
                    new_row = {"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "血圧上2": u2, "血圧下2": d2}
                    conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.success("保存！"); st.rerun()

    weight_tab_idx = 2 if user == "克己" else 1
    with tabs[weight_tab_idx]:
        show_weight = True
        if user == "祐介":
            w_pw = st.text_input("体重画面パスワード", type="password")
            if st.button("🔓 体重管理画面を表示"):
                if w_pw == "yawaranr": st.session_state.weight_auth = True
                else: st.error("パスワードが違います")
            if not st.session_state.get("weight_auth", False): show_weight = False
        
        if show_weight:
            with st.form("weight_form"):
                weight = st.number_input("体重 (kg)", 30.0, 150.0, 60.0, step=0.1)
                if st.form_submit_button("⚖️ 記録"):
                    new_row = {"日付": str(date.today()), "体重": weight}
                    conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.success("保存！"); st.rerun()

# --- 6. 履歴表示 (ユーザーごとに列を絞り込む) ---
if not df_clean.empty:
    st.subheader("📋 履歴一覧 (1日1最新データ)")
    if user == "テト":
        # 猫用テーブル項目
        display_cols = ["日付", "ごはんの量", "うんち回数", "運動量", "総合元気度", "メモ"]
    else:
        # 人間用テーブル項目
        display_cols = ["日付", "睡眠時間", "体調", "総合実績", "行動意欲", "メモ"]
        if "体重" in df_clean.columns: display_cols.append("体重")
        if user == "克己": display_cols.extend(["血圧上1", "血圧下1", "血圧上2", "血圧下2"])

    # 実際に存在する列だけを抽出
    existing_cols = [c for c in display_cols if c in df_clean.columns]
    st.dataframe(df_clean[existing_cols].sort_values("日付", ascending=False), use_container_width=True)

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
except:
    raw_df = pd.DataFrame()
    df_clean = pd.DataFrame()

# ヘッダー
st.title(f"🐾 {user}ちゃんの管理" if user == "テト" else f"👋 {user}さんの管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.weight_auth = False
    st.rerun()

# --- 4. グラフ ---
if not df_clean.empty:
    st.subheader("📈 体調トレンド")
    gdf = df_clean.copy()
    base = alt.Chart(gdf).encode(x=alt.X('日付:N', title='日付', axis=alt.Axis(labelAngle=-45)))
    if user == "テト":
        l1 = base.mark_line(strokeWidth=4, color='#FF69B4', point=True).encode(y=alt.Y('総合元気度:Q', scale=alt.Scale(domain=[0, 10])))
        st.altair_chart(l1, use_container_width=True)
    else:
        cols_map = {"総合実績": '#1f77b4', "行動意欲": '#ff7f0e', "体調": '#2ca02c', "睡眠時間": '#d62728'}
        lines = [base.mark_line(color=c, point=True).encode(y=alt.Y(f'{k}:Q', scale=alt.Scale(domain=[0, 10]))) for k, c in cols_map.items() if k in gdf.columns]
        if lines: st.altair_chart(alt.layer(*lines), use_container_width=True)

st.divider()

# --- 5. 入力セクション ---
if user == "テト":
    with st.form("cat_form"):
        st.subheader("🐱 猫用入力")
        c1, c2, c3 = st.columns(3)
        with c1:
            food = st.selectbox("ごはんの量", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
            water = st.slider("水分補給", 1, 10, 5)
            vomit = st.checkbox("嘔吐・毛玉あり")
        with c2:
            poo_s = st.selectbox("うんちの状態", ["かなり硬い", "少し硬い", "普通", "柔らかい", "かなり柔らかい"], index=2)
            poo_c = st.number_input("うんち回数", 0, 10, 1)
            pee_c = st.slider("おしっこ回数", 0, 10, 2)
        with c3:
            genki = st.slider("総合元気度", 1, 10, 8)
            active = st.slider("運動量", 1, 10, 5)
            brush = st.checkbox("ブラッシング・ケア済")
        memo_cat = st.text_area("様子メモ")
        if st.form_submit_button("🐾 記録を保存"):
            new_row = {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, "総合元気度": genki, "メモ": memo_cat}
            updated = pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(spreadsheet=url, worksheet=t_month, data=updated)
            st.success("保存完了"); st.rerun()
else:
    t1, t2 = st.tabs(["🚶 体調", "⚖️ 体重"])
    with t1:
        with st.form("h_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                wake, sleep, sl_h = st.text_input("起床", "7:00"), st.text_input("就寝", "23:00"), st.number_input("睡眠h", 0.0, 24.0, 7.0)
            with c2:
                s_q, s_w, cond = st.slider("寝つき", 1, 10, 7), st.slider("寝起き", 1, 10, 7), st.slider("体調", 1, 10, 7)
            with c3:
                g, a, f = st.slider("実績", 1, 10, 5), st.slider("意欲", 1, 10, 5), st.slider("食生活", 1, 10, 6)
            memo = st.text_area("メモ")
            if st.form_submit_button("🚀 保存"):
                new_row = {"日付": str(date.today()), "起床時間": wake, "就寝時間": sleep, "睡眠時間": sl_h, "寝つき": s_q, "寝起き": s_w, "体調": cond, "総合実績": g, "行動意欲": a, "食生活": f, "メモ": memo}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("保存完了"); st.rerun()
    with t2:
        if user == "祐介":
            w_pw = st.text_input("体重解除パスワード", type="password")
            if st.button("🔓 解除") and w_pw == "yawaranr": st.session_state.weight_auth = True
        if user != "祐介" or st.session_state.weight_auth:
            with st.form("w_form"):
                weight = st.number_input("体重(kg)", 30.0, 150.0, 60.0)
                if st.form_submit_button("⚖️ 記録"):
                    conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame({"日付": [str(date.today())], "体重": [weight]})], ignore_index=True))
                    st.success("保存完了"); st.rerun()

st.divider()

# --- 6. 編集・削除・履歴機能 ---
if not df_clean.empty:
    st.subheader("📋 履歴の管理（編集・削除）")
    # ユーザー別列設定
    if user == "テト":
        cols = ["日付", "ごはんの量", "水分補給", "おしっこ回数", "うんち回数", "うんちの状態", "毛玉嘔吐", "運動量", "ブラッシング", "総合元気度", "メモ"]
    else:
        cols = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "総合実績", "行動意欲", "食生活", "メモ", "体重"]
    
    existing = [c for c in cols if c in df_clean.columns]
    target_date = st.selectbox("編集・削除する日付を選択", df_clean['日付'].unique()[::-1])
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ 選択した日を削除", use_container_width=True):
            updated_df = raw_df[raw_df['日付'] != target_date]
            conn.update(spreadsheet=url, worksheet=t_month, data=updated_df)
            st.warning(f"{target_date}のデータを削除しました"); st.rerun()
            
    with c2:
        if st.button("✏️ この日を編集する", use_container_width=True):
            st.session_state.edit_mode = True
            st.session_state.edit_date = target_date

    if st.session_state.get("edit_mode"):
        edit_data = df_clean[df_clean['日付'] == st.session_state.edit_date].iloc[0]
        with st.expander(f"📝 {st.session_state.edit_date} のデータを編集中", expanded=True):
            new_edit_df = st.data_editor(pd.DataFrame([edit_data]))
            if st.button("✅ 変更を確定して保存"):
                raw_df = raw_df[raw_df['日付'] != st.session_state.edit_date]
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, new_edit_df], ignore_index=True))
                st.session_state.edit_mode = False
                st.success("修正しました"); st.rerun()

    st.dataframe(df_clean[existing].sort_values("日付", ascending=False), use_container_width=True)

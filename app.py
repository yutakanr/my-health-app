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

# --- 3. 共通関数とデータ読み込み ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
t_month = date.today().strftime("%Y-%m")

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if not df.empty and '日付' in df.columns:
            df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
        return df
    except: return pd.DataFrame()

def format_drive_url(raw_url):
    if pd.isna(raw_url) or "id=" not in str(raw_url): return None
    file_id = str(raw_url).split("id=")[-1].split("&")[0]
    return f"https://drive.google.com/uc?id={file_id}"

def show_data_footer(display_df, filter_cols, key_suffix):
    if not display_df.empty:
        st.divider()
        st.subheader("📋 記録一覧と削除")
        existing_cols = [c for c in filter_cols if c in display_df.columns]
        target_df = display_df[existing_cols].copy()
        
        target_date = st.selectbox("削除する日付を選択", target_df['日付'].unique()[::-1], key=f"sb_{key_suffix}")
        if st.button("🗑️ 選択した日のデータを削除", key=f"del_{key_suffix}"):
            # 簡易削除ロジック: 該当月全データから該当日のデータを除外して上書き
            all_data = load_data(t_month)
            new_df = all_data[all_data['日付'] != target_date]
            conn.update(spreadsheet=url, worksheet=t_month, data=new_df)
            st.cache_data.clear(); st.success("削除しました"); st.rerun()
        
        st.dataframe(target_df.sort_values("日付", ascending=False), use_container_width=True)

# ヘッダー
st.title(f"🐾 {user}ちゃんの管理" if user == "テト" else f"👋 {user}さんの管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.weight_auth = False
    st.rerun()

# --- 4. タブ設定 ---
tab_labels = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己": tab_labels.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_labels)

# --- タブ1: 体調記録 ---
with tabs[0]:
    df_main = load_data(t_month)
    
    if user == "テト":
        st.subheader("✨ 今日のテトちゃん")
        col_m, col_b = st.columns([2, 1])
        with col_m: st.info("写真はGoogleフォームからアップしてね！")
        with col_b: st.link_button("📷 写真を保存", "あなたのフォームURL", use_container_width=True)

        with st.form("teto_form"):
            st.markdown("##### 🍖 食事・水分 / 🚽 トイレ")
            c1, c2, c3 = st.columns(3)
            with c1:
                food = st.select_slider("ごはん", options=["かなり少", "少", "普通", "多", "かなり多"], value="普通")
                water = st.slider("水分 (0-10)", 0, 10, 5)
            with c2:
                poo_s = st.selectbox("うんち状態", ["普通", "硬い", "柔らかい"])
                poo_c = st.number_input("うんち回数", 0, 10, 1)
            with c3:
                pee_c = st.number_input("おしっこ回数", 0, 10, 2)
                vomit = st.checkbox("毛玉嘔吐")
            
            st.markdown("##### 🏃 活動・元気")
            c4, c5 = st.columns(2)
            with c4: genki = st.slider("元気度", 0, 10, 8)
            with c5: active = st.slider("運動量", 0, 10, 5); brush = st.checkbox("ブラッシング")
            
            memo = st.text_area("メモ")
            if st.form_submit_button("🐾 記録を保存"):
                new_row = {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, "総合元気度": genki, "メモ": memo}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True))
                st.cache_data.clear(); st.rerun()

        if not df_main.empty:
            st.divider()
            sel_date = st.selectbox("過去の記録と写真", df_main['日付'].unique()[::-1])
            d_col, p_col = st.columns([1, 1])
            with d_col:
                row = df_main[df_main['日付'] == sel_date].iloc[0]
                st.write(f"🌟 元気: {row.get('総合元気度', '-')}/10  |  🍚 ごはん: {row.get('ごはんの量', '-')}")
                st.write(f"📝 メモ: {row.get('メモ', '-')}")
            with p_col:
                df_p = load_data("フォームの回答 1")
                if not df_p.empty:
                    p_row = df_p[df_p['日付'].astype(str).str.contains(str(sel_date))]
                    if not p_row.empty:
                        st.image(format_drive_url(p_row.iloc[0]['今日の写真']), use_container_width=True)
            show_data_footer(df_main, ["日付", "ごはんの量", "水分補給", "おしっこ回数", "うんち回数", "うんちの状態", "毛玉嘔吐", "運動量", "ブラッシング", "総合元気度", "メモ"], "cat")

    else:
        # 人間の体調入力フォーム
        st.subheader("📝 本日の体調")
        with st.form("h_form"):
            c1, c2, c3 = st.columns(3)
            with c1: wake = st.text_input("起床", "7:00"); sleep = st.text_input("就寝", "23:00"); sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
            with c2: s_q = st.slider("寝つき", 0, 10, 7); s_w = st.slider("寝起き", 0, 10, 7); cond = st.slider("体調", 0, 10, 7)
            with c3: g = st.slider("総合", 0, 10, 5); a = st.slider("意欲", 0, 10, 5); f = st.slider("食事", 0, 10, 6)
            memo_h = st.text_area("メモ")
            if st.form_submit_button("🚀 保存"):
                new_row = {"日付": str(date.today()), "起床時間": wake, "就寝時間": sleep, "睡眠時間": sl_h, "寝つき": s_q, "寝起き": s_w, "体調": cond, "総合実績": g, "行動意欲": a, "食生活": f, "メモ": memo_h}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        show_data_footer(df_main, ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "行動意欲", "食生活", "総合実績", "メモ"], "hum")

# --- タブ2: 血圧 (克己のみ) ---
if user == "克己":
    with tabs[1]:
        df_bp = load_data(t_month)
        with st.form("bp_form"):
            c1, c2 = st.columns(2)
            with c1: u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
            with c2: u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
            memo_bp = st.text_area("メモ")
            if st.form_submit_button("🩸 血圧保存"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_bp, pd.DataFrame([{"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "血圧上2": u2, "血圧下2": d2, "メモ": memo_bp}])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        show_data_footer(df_bp, ["日付", "血圧上1", "血圧下1", "血圧上2", "血圧下2", "メモ"], "bp")

# --- タブ3: 体重管理 ---
w_idx = 2 if user == "克己" else 1
with tabs[w_idx]:
    if user == "祐介" and not st.session_state.weight_auth:
        pw = st.text_input("体重PW", type="password")
        if st.button("🔓 解除"):
            if pw == "yawaranr": st.session_state.weight_auth = True; st.rerun()
    else:
        df_w = load_data(t_month)
        with st.form("w_form"):
            weight = st.number_input("体重(kg)", 30.0, 150.0, 60.0, step=0.1)
            w_memo = st.text_area("メモ") if user != "祐介" else ""
            if st.form_submit_button("⚖️ 体重保存"):
                new_w = {"日付": str(date.today()), "体重": weight}
                if user != "祐介": new_w["メモ"] = w_memo
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_w, pd.DataFrame([new_w])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        w_cols = ["日付", "体重"] if user == "祐介" else ["日付", "体重", "メモ"]
        show_data_footer(df_w, w_cols, "weight")

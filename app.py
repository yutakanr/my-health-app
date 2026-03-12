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

# --- 画像変換ヘルパー ---
def image_to_base64(uploaded_file):
    if uploaded_file is None: return ""
    try:
        img = Image.open(uploaded_file)
        if img.mode != "RGB": img = img.convert("RGB")
        img.thumbnail((500, 500))
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    except: return ""

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

# --- 3. 共通ロジック ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if df is not None and not df.empty:
            df = df.dropna(how='all')
            if '日付' in df.columns:
                df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
                return df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
        return pd.DataFrame()
    except: return pd.DataFrame()

def save_entry(sheet_name, new_data_dict):
    existing_df = load_data(sheet_name)
    target_date = str(new_data_dict["日付"])
    if not existing_df.empty and target_date in existing_df["日付"].values:
        idx = existing_df[existing_df["日付"] == target_date].index[0]
        for col, val in new_data_dict.items():
            if val is not None and val != "" and val is not False:
                existing_df.at[idx, col] = val
        final_df = existing_df
    else:
        final_df = pd.concat([existing_df, pd.DataFrame([new_data_dict])], ignore_index=True)
    conn.update(spreadsheet=url, worksheet=sheet_name, data=final_df.fillna(""))
    st.cache_data.clear()

# --- 4. UIヘッダー ---
c_l, c_c, c_r = st.columns([1.5, 2, 1.5])
with c_l:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()
    st.markdown(f"#### {'🐾 ' + user if user == 'テト' else '👋 ' + user + 'さん'}")
with c_c:
    today = date.today()
    month_opts = [(today.replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
    selected_month = st.selectbox("📅 表示月", month_opts, label_visibility="collapsed")

# --- タブ設定 ---
tabs = st.tabs(["🚶 体調記録", "🩸 血圧管理", "⚖️ 体重管理"] if user == "克己" else ["🚶 体調記録", "⚖️ 体重管理"])

# --- タブ1: 体調記録 ---
with tabs[0]:
    df_main = load_data(selected_month)
    if selected_month == today.strftime("%Y-%m"):
        with st.form("main_form", clear_on_submit=True):
            if user == "テト":
                c1, c2, c3 = st.columns(3)
                with c1:
                    food = st.select_slider("ごはん", ["かなり少", "少", "普通", "多", "かなり多"], "普通")
                    water = st.slider("水分補給", 0, 10, 5)
                with c2:
                    poo_s = st.selectbox("うんちの状態", ["普通", "少し硬い", "かなり硬い", "柔らかい", "かなり柔らかい"])
                    poo_c = st.number_input("うんち回数", 0, 10, 1)
                with c3:
                    pee_c = st.number_input("おしっこ回数", 0, 10, 2)
                    vomit = st.checkbox("毛玉嘔吐")
                c4, c5 = st.columns(2)
                with c4: genki = st.slider("元気度", 0, 10, 8)
                with c5: active = st.slider("運動量", 0, 10, 5); brush = st.checkbox("ブラッシング")
                t_img = st.file_uploader("📸 写真", type=['png', 'jpg', 'jpeg'])
                memo = st.text_area("メモ")
                if st.form_submit_button("🐾 記録を保存", use_container_width=True, type="primary"):
                    save_entry(selected_month, {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, "総合元気度": genki, "画像URL": image_to_base64(t_img), "メモ": memo})
                    st.rerun()
            else:
                c1, c2, c3 = st.columns(3)
                with c1:
                    wake = st.text_input("起床", "7:00")
                    sleep = st.text_input("就寝", "23:00")
                    sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
                with c2:
                    s_q = st.slider("寝つき", 0, 10, 7)
                    s_w = st.slider("寝起き", 0, 10, 7)
                    cond = st.slider("体調", 0, 10, 7)
                with c3:
                    g = st.slider("総合実績", 0, 10, 5)
                    a = st.slider("行動意欲", 0, 10, 5)
                    f = st.slider("食生活", 0, 10, 6)
                memo = st.text_area("メモ")
                if st.form_submit_button("🚀 記録を保存", use_container_width=True, type="primary"):
                    save_entry(selected_month, {"日付": str(date.today()), "起床時間": wake, "就寝時間": sleep, "睡眠時間": sl_h, "寝つき": s_q, "寝起き": s_w, "体調": cond, "総合実績": g, "行動意欲": a, "食生活": f, "メモ": memo})
                    st.rerun()
    
    if not df_main.empty:
        st.subheader("📈 トレンド（体調・活動）")
        # --- ここで「食生活」をグラフ項目に含める ---
        all_cols = ["体調", "睡眠時間", "総合実績", "行動意欲", "食生活", "寝つき", "寝起き", "水分補給", "総合元気度", "運動量"]
        v_cols = [c for c in all_cols if c in df_main.columns]
        if v_cols:
            m_df = df_main.melt(id_vars=['日付'], value_vars=v_cols).dropna()
            chart = alt.Chart(m_df).mark_line(point=True).encode(
                x='日付:N',
                y=alt.Y('value:Q', title='数値'),
                color=alt.Color('variable:N', title='項目')
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)

# --- タブ2: 血圧 (克己のみ) ---
if user == "克己":
    with tabs[1]:
        df_bp = load_data(selected_month)
        with st.form("bp_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
            with c2:
                u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
            with c3:
                p1 = st.number_input("脈拍1", 0, 200, 70)
                p2 = st.number_input("脈拍2", 0, 200, 70)
            if st.form_submit_button("🩸 保存", use_container_width=True):
                save_entry(selected_month, {"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "血圧上2": u2, "血圧下2": d2, "脈拍1": p1, "脈拍2": p2})
                st.rerun()
        
        if not df_bp.empty:
            st.subheader("📈 血圧推移")
            bp_c = [c for c in ["血圧上1", "血圧下1", "血圧上2", "血圧下2"] if c in df_bp.columns]
            if bp_c:
                m_bp = df_bp.melt(id_vars=['日付'], value_vars=bp_c).dropna()
                st.altair_chart(alt.Chart(m_bp).mark_line(point=True).encode(
                    x='日付:N', y=alt.Y('value:Q', scale=alt.Scale(zero=False)), color='variable:N'
                ).properties(height=250), use_container_width=True)

            st.subheader("💓 脈拍トレンド")
            pulse_c = [c for c in ["脈拍1", "脈拍2"] if c in df_bp.columns]
            if pulse_c:
                m_p = df_bp.melt(id_vars=['日付'], value_vars=pulse_c).dropna()
                p_chart = alt.Chart(m_p).mark_line(point=True).encode(
                    x='日付:N', y=alt.Y('value:Q', title='bpm', scale=alt.Scale(zero=False)),
                    color=alt.Color('variable:N', scale=alt.Scale(range=['#00CC96', '#AB63FA']))
                ).properties(height=200)
                st.altair_chart(p_chart, use_container_width=True)

# --- タブ3: 体重 ---
with tabs[-1]:
    if user == "祐介" and not st.session_state.weight_auth:
        pw = st.text_input("体重PW", type="password")
        if st.button("🔓 解除"):
            if pw == "yawaranr": st.session_state.weight_auth = True; st.rerun()
    else:
        df_w = load_data(selected_month)
        with st.form("w_form"):
            w_def = 6.0 if user == "テト" else 60.0
            weight = st.number_input("体重(kg)", 3.0, 150.0, w_def, step=0.1)
            if st.form_submit_button("⚖️ 保存"):
                save_entry(selected_month, {"日付": str(date.today()), "体重": weight})
                st.rerun()
        if not df_w.empty and '体重' in df_w.columns:
            st.subheader("📈 体重推移")
            st.altair_chart(alt.Chart(df_w.dropna(subset=['体重'])).mark_line(point=True, color='orange').encode(x='日付:N', y=alt.Y('体重:Q', scale=alt.Scale(zero=False))).properties(height=300), use_container_width=True)

# --- 5. 履歴表示 ---
st.divider()
all_df = load_data(selected_month)
if not all_df.empty:
    st.subheader(f"📋 {selected_month} の履歴")
    # 履歴詳細と編集・削除機能の復元
    target_date = st.selectbox("詳細を見る日付を選択", all_df['日付'].unique()[::-1])
    row = all_df[all_df['日付'] == target_date].iloc[0]
    
    if "画像URL" in row and str(row.get("画像URL")).startswith("data:image"):
        st.image(row["画像URL"], width=450)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ データを削除", use_container_width=True):
            conn.update(spreadsheet=url, worksheet=selected_month, data=all_df[all_df['日付'] != target_date])
            st.cache_data.clear(); st.rerun()
    with c2:
        if st.button("✏️ データを編集", use_container_width=True):
            st.session_state.edit_mode, st.session_state.edit_date = True, target_date

    if st.session_state.get("edit_mode") and st.session_state.edit_date == target_date:
        edit_df = st.data_editor(pd.DataFrame([row]))
        if st.button("✅ 修正を確定"):
            save_entry(selected_month, edit_df.iloc[0].to_dict())
            st.session_state.edit_mode = False; st.rerun()
            
    st.dataframe(all_df.sort_values("日付", ascending=False), use_container_width=True)

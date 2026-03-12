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

# --- 画像変換用のヘルパー関数 ---
def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail((500, 500)) 
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=70)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            st.error(f"画像の処理に失敗しました: {e}")
            return ""
    return ""

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

# --- 3. 共通設定と月選択 ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"

st.sidebar.header("🗓️ 表示設定")
today = date.today()
# 直近12ヶ月分を選択肢として生成
month_options = [(today.replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
selected_month = st.sidebar.selectbox("表示する月を選択", month_options)

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if not df.empty:
            df = df.dropna(how='all')
            if '日付' in df.columns:
                df = df.dropna(subset=['日付'])
                df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
                return df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
        return df
    except Exception:
        return pd.DataFrame()

# 上書き防止保存ロジック
def save_entry(sheet_name, new_data_dict):
    existing_df = load_data(sheet_name)
    target_date = new_data_dict["日付"]
    if not existing_df.empty:
        if target_date in existing_df["日付"].values:
            idx = existing_df[existing_df["日付"] == target_date].index[0]
            for col, val in new_data_dict.items():
                existing_df.at[idx, col] = val
            final_df = existing_df
        else:
            final_df = pd.concat([existing_df, pd.DataFrame([new_data_dict])], ignore_index=True)
    else:
        final_df = pd.DataFrame([new_data_dict])
    conn.update(spreadsheet=url, worksheet=sheet_name, data=final_df)
    st.cache_data.clear()

# --- 4. フッター（表と編集・削除） ---
def show_data_footer(display_df, filter_cols, key_suffix):
    if not display_df.empty:
        st.divider()
        st.subheader(f"📋 {selected_month} の一覧と詳細")
        
        target_date = st.selectbox("詳細を見る日付を選択", display_df['日付'].unique()[::-1], key=f"sb_{key_suffix}")
        selected_row = display_df[display_df['日付'] == target_date].iloc[0]
        
        # 写真表示の復元
        if "画像URL" in selected_row and pd.notna(selected_row["画像URL"]) and str(selected_row["画像URL"]).startswith("data:image"):
            st.info(f"📸 {target_date} の写真")
            st.image(selected_row["画像URL"], use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ データを削除", use_container_width=True, key=f"del_{key_suffix}"):
                raw = load_data(selected_month)
                updated_df = raw[raw['日付'] != target_date]
                conn.update(spreadsheet=url, worksheet=selected_month, data=updated_df)
                st.cache_data.clear(); st.rerun()
        with c2:
            if st.button("✏️ データを編集", use_container_width=True, key=f"edit_{key_suffix}"):
                st.session_state.edit_mode, st.session_state.edit_date = True, target_date

        if st.session_state.get("edit_mode") and st.session_state.edit_date == target_date:
            with st.expander(f"📝 {target_date} を編集中", expanded=True):
                current_cols = [c for c in filter_cols if c in display_df.columns]
                edit_df = st.data_editor(pd.DataFrame([selected_row[current_cols]]))
                if st.button("✅ 修正を確定", key=f"confirm_{key_suffix}"):
                    save_entry(selected_month, edit_df.iloc[0].to_dict())
                    st.session_state.edit_mode = False; st.rerun()
        
        view_cols = [c for c in filter_cols if c in display_df.columns]
        st.dataframe(display_df[view_cols].sort_values("日付", ascending=False), use_container_width=True)

# --- 🚀 メイン画面 ---
st.title(f"🐾 {user}の体調管理" if user == "テト" else f"👋 {user}さんの体調管理")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False; st.rerun()

tab_labels = ["🚶 体調", "⚖️ 体重"]
if user == "克己": tab_labels.insert(1, "🩸 血圧")
tabs = st.tabs(tab_labels)

# --- タブ1: 体調記録 ---
with tabs[0]:
    df_main = load_data(selected_month)
    if selected_month == today.strftime("%Y-%m"):
        with st.form("main_form"):
            if user == "テト":
                c1, c2 = st.columns(2)
                with c1: food = st.select_slider("ごはん", ["かなり少", "少", "普通", "多", "かなり多"], "普通"); water = st.slider("水分補給", 0, 10, 5)
                with c2: poo_s = st.selectbox("うんち状態", ["普通", "少し硬い", "かなり硬い", "柔らかい", "かなり柔らかい"]); poo_c = st.number_input("うんち回数", 0, 10, 1)
                teto_img = st.file_uploader("📸 今日のベストショット", type=['png', 'jpg', 'jpeg'])
                memo = st.text_area("メモ")
                if st.form_submit_button("🐾 記録を保存"):
                    save_entry(selected_month, {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "うんちの状態": poo_s, "うんち回数": poo_c, "画像URL": image_to_base64(teto_img), "メモ": memo})
                    st.rerun()
            else:
                c1, c2 = st.columns(2)
                with c1: cond = st.slider("体調", 0, 10, 7); sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
                with c2: g = st.slider("総合実績", 0, 10, 5); memo = st.text_area("メモ")
                if st.form_submit_button("🚀 記録を保存"):
                    save_entry(selected_month, {"日付": str(date.today()), "体調": cond, "睡眠時間": sl_h, "総合実績": g, "メモ": memo})
                    st.rerun()
    
    if not df_main.empty:
        st.subheader("📈 トレンド")
        h_cols = ["体調", "睡眠時間", "総合実績", "水分補給"]
        v_cols = [c for c in h_cols if c in df_main.columns]
        if v_cols:
            m_df = df_main.melt(id_vars=['日付'], value_vars=v_cols).dropna()
            st.altair_chart(alt.Chart(m_df).mark_line(point=True).encode(x='日付:N', y='数値:Q', color='項目:N').properties(height=300), use_container_width=True)
        show_data_footer(df_main, ["日付", "体調", "睡眠時間", "総合実績", "ごはんの量", "水分補給", "うんちの状態", "画像URL", "メモ"], "main")

# --- タブ: 血圧 (克己のみ) ---
if user == "克己":
    with tabs[1]:
        df_bp = load_data(selected_month)
        if selected_month == today.strftime("%Y-%m"):
            with st.form("bp_form"):
                c1, c2 = st.columns(2)
                with c1: 
                    u1, d1 = st.number_input("血圧上1", 0, 250, 120), st.number_input("血圧下1", 0, 200, 80)
                    p1 = st.number_input("脈拍1", 0, 200, 70)
                with c2: 
                    u2, d2 = st.number_input("血圧上2", 0, 250, 120), st.number_input("血圧下2", 0, 200, 80)
                    p2 = st.number_input("脈拍2", 0, 200, 70)
                if st.form_submit_button("🩸 血圧を保存"):
                    save_entry(selected_month, {"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "脈拍1": p1, "血圧上2": u2, "血圧下2": d2, "脈拍2": p2})
                    st.rerun()
        
        if not df_bp.empty:
            st.subheader("📈 血圧トレンド")
            bp_cols = [c for c in ["血圧上1", "血圧下1", "血圧上2", "血圧下2"] if c in df_bp.columns]
            if bp_cols:
                m_bp = df_bp.melt(id_vars=['日付'], value_vars=bp_cols).dropna()
                st.altair_chart(alt.Chart(m_bp).mark_line(point=True).encode(
                    x='日付:N', y=alt.Y('数値:Q', scale=alt.Scale(zero=False), title="血圧"), 
                    color=alt.Color('項目:N', scale=alt.Scale(scheme='category10'))
                ).properties(height=250), use_container_width=True)
            
            st.subheader("💓 脈拍トレンド")
            pulse_cols = [c for c in ["脈拍1", "脈拍2"] if c in df_bp.columns]
            if pulse_cols:
                m_pulse = df_bp.melt(id_vars=['日付'], value_vars=pulse_cols).dropna()
                st.altair_chart(alt.Chart(m_pulse).mark_line(point=True).encode(
                    x='日付:N', y=alt.Y('数値:Q', scale=alt.Scale(zero=False), title="脈拍"), 
                    color=alt.Color('項目:N', scale=alt.Scale(scheme='set2'))
                ).properties(height=250), use_container_width=True)
            
            show_data_footer(df_bp, ["日付", "血圧上1", "血圧下1", "脈拍1", "血圧上2", "血圧下2", "脈拍2"], "bp")

# --- タブ: 体重 ---
w_idx = 2 if user == "克己" else 1
with tabs[w_idx]:
    if user == "祐介" and not st.session_state.weight_auth:
        pw = st.text_input("体重PW", type="password")
        if st.button("🔓 解除"):
            if pw == "yawaranr": st.session_state.weight_auth = True; st.rerun()
    else:
        df_w = load_data(selected_month)
        if selected_month == today.strftime("%Y-%m"):
            with st.form("w_form"):
                weight = st.number_input("体重(kg)", 3.0, 150.0, 6.0 if user=="テト" else 60.0, step=0.1)
                if st.form_submit_button("⚖️ 体重を保存"):
                    save_entry(selected_month, {"日付": str(date.today()), "体重": weight})
                    st.rerun()
        if not df_w.empty and '体重' in df_w.columns:
            st.altair_chart(alt.Chart(df_w.dropna(subset=['体重'])).mark_line(point=True, color='orange').encode(x='日付:N', y=alt.Y('体重:Q', scale=alt.Scale(zero=False))).properties(height=300), use_container_width=True)
        show_data_footer(df_w, ["日付", "体重"], "weight")

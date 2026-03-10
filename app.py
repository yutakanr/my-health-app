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
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False

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

# --- 3. データ読み込み関数 ---
user = st.session_state.current_user
spreadsheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=0"

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if not df.empty and '日付' in df.columns:
            df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
        return df
    except:
        return pd.DataFrame()

# GoogleドライブのURLを表示用に変換
def format_drive_url(raw_url):
    if pd.isna(raw_url) or "id=" not in str(raw_url): return None
    file_id = str(raw_url).split("id=")[-1].split("&")[0]
    return f"https://drive.google.com/uc?id={file_id}"

# --- メイン画面 ---
st.title(f"🐾 {user}ちゃんの管理" if user == "テト" else f"👋 {user}さんの管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.weight_auth = False
    st.rerun()

st.divider()

# 共通フッター（編集・削除）
def show_data_footer(display_df, filter_cols, key_suffix):
    if not display_df.empty:
        st.divider()
        st.subheader("📋 データの編集・削除と一覧")
        existing_cols = [c for c in filter_cols if c in display_df.columns]
        target_df = display_df[existing_cols].copy()
        target_date = st.selectbox("編集・削除する日付を選択", target_df['日付'].unique()[::-1], key=f"sb_{key_suffix}")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ データを削除", use_container_width=True, key=f"del_{key_suffix}"):
                # 削除処理（実際は全体から特定の日付以外を上書き）
                # ここでは簡易化のためメッセージのみ（実装済みコードを推奨）
                st.warning("削除機能はスプレッドシートの全体更新が必要です")
        
        st.write("📖 記録一覧")
        st.dataframe(target_df.sort_values("日付", ascending=False), use_container_width=True)

# タブ切り替え
t_month = date.today().strftime("%Y-%m")
tab_labels = ["🚶 体調記録", "⚖️ 体重管理"]
if user == "克己": tab_labels.insert(1, "🩸 血圧管理")
tabs = st.tabs(tab_labels)

# --- 4-1. 体調記録タブ ---
with tabs[0]:
    df_main = load_data(t_month)
    
    if user == "テト":
        st.subheader("✨ テトちゃんの今日の様子")
        
        # 写真アップロード誘導
        col_info, col_btn = st.columns([2, 1])
        with col_info:
            st.info("写真はGoogleフォームからアップしてね。ここに自動で表示されるよ！")
        with col_btn:
            form_url = "https://docs.google.com/forms/d/e/あなたのフォームID/viewform"
            st.link_button("📷 今日の写真を保存", form_url, use_container_width=True)

        # 改善された入力フォーム
        with st.expander("📝 記録を入力する", expanded=True):
            with st.form("cat_form_pro"):
                st.markdown("#### 🍖 食事・水分 / 🚽 トイレ")
                c1, c2, c3 = st.columns(3)
                with c1:
                    food = st.select_slider("ごはん", options=["かなり少", "少", "普通", "多", "かなり多"], value="普通")
                    water = st.slider("水分 (0-10)", 0, 10, 5)
                with c2:
                    poo_s = st.selectbox("うんちの状態", ["普通", "硬い", "柔らかい"])
                    poo_c = st.number_input("うんち回数", 0, 5, 1)
                with c3:
                    pee_c = st.number_input("おしっこ回数", 0, 5, 2)
                    genki = st.slider("元気度", 0, 10, 8)
                
                memo_cat = st.text_area("一言メモ")
                if st.form_submit_button("🐾 記録を保存"):
                    new_row = {"日付": str(date.today()), "ごはんの量": food, "水分補給": water, "うんちの状態": poo_s, "うんち回数": poo_c, "おしっこ回数": pee_c, "総合元気度": genki, "メモ": memo_cat}
                    conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True))
                    st.cache_data.clear(); st.rerun()

        # 写真と履歴の表示
        if not df_main.empty:
            st.divider()
            st.subheader("📊 過去の記録と写真")
            selected_date = st.selectbox("表示する日付を選択", df_main['日付'].unique()[::-1], key="view_date")
            
            d_col, p_col = st.columns([1, 1])
            with d_col:
                day_data = df_main[df_main['日付'] == selected_date].iloc[0]
                st.write(f"**日付:** {selected_date}")
                st.write(f"**ごはん:** {day_data.get('ごはんの量', '-')}")
                st.write(f"**元気度:** {day_data.get('総合元気度', '-')}/10")
                st.write(f"**メモ:** {day_data.get('メモ', '-')}")

            with p_col:
                df_photo = load_data("フォームの回答 1") # フォームのシート名
                if not df_photo.empty:
                    # 日付で照合（フォーム側の日付列名を確認してね）
                    photo_row = df_photo[df_photo['日付'].astype(str).str.contains(str(selected_date))]
                    if not photo_row.empty:
                        img_url = format_drive_url(photo_row.iloc[0]['今日の写真'])
                        if img_url: st.image(img_url, caption=f"{selected_date} のテト", use_container_width=True)
                    else: st.warning("この日の写真はまだないよ")
    
    else:
        # 人間の体調管理（変更なし）
        with st.form("h_form"):
            c1, c2, c3 = st.columns(3)
            with c1: wake = st.text_input("起床", "7:00"); sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
            with c2: cond = st.slider("体調", 0, 10, 7); g = st.slider("総合実績", 0, 10, 5)
            with c3: f = st.slider("食生活", 0, 10, 6)
            memo_h = st.text_area("メモ")
            if st.form_submit_button("🚀 保存"):
                new_row = {"日付": str(date.today()), "睡眠時間": sl_h, "体調": cond, "総合実績": g, "食生活": f, "メモ": memo_h}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        show_data_footer(df_main, ["日付", "睡眠時間", "体調", "総合実績", "食生活", "メモ"], "hum")

# --- 4-2. 血圧管理タブ (克己のみ) ---
if user == "克己":
    with tabs[1]:
        df_bp = load_data(t_month)
        with st.form("bp_form"):
            c1, c2 = st.columns(2)
            with c1: u1, d1 = st.number_input("血圧上", 0, 200, 120), st.number_input("血圧下", 0, 150, 80)
            bp_memo = st.text_area("メモ")
            if st.form_submit_button("🩸 保存"):
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_bp, pd.DataFrame([{"日付": str(date.today()), "血圧上1": u1, "血圧下1": d1, "メモ": bp_memo}])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        show_data_footer(df_bp, ["日付", "血圧上1", "血圧下1", "メモ"], "bp")

# --- 4-3. 体重管理タブ (祐介メモ非表示対応) ---
w_tab_idx = 2 if user == "克己" else 1
with tabs[w_tab_idx]:
    if user == "祐介" and not st.session_state.weight_auth:
        w_pw = st.text_input("PW", type="password")
        if st.button("🔓 解除"):
            if w_pw == "yawaranr": st.session_state.weight_auth = True; st.rerun()
    else:
        df_w = load_data(t_month)
        with st.form("w_form"):
            weight = st.number_input("体重(kg)", 30.0, 120.0, 60.0)
            w_memo = st.text_area("メモ") if user != "祐介" else ""
            if st.form_submit_button("⚖️ 保存"):
                new_w = {"日付": str(date.today()), "体重": weight}
                if user != "祐介": new_w["メモ"] = w_memo
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([df_w, pd.DataFrame([new_w])], ignore_index=True))
                st.cache_data.clear(); st.rerun()
        
        # 祐介ならメモを表示しない
        w_cols = ["日付", "体重"] if user == "祐介" else ["日付", "体重", "メモ"]
        show_data_footer(df_w, w_cols, "weight")

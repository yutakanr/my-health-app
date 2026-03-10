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

# セッション状態の初期化
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

# ヘッダー
st.title(f"🐾 {user}ちゃんの管理" if user == "テト" else f"👋 {user}さんの管理")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. メインコンテンツ ---
tabs = st.tabs(["🚶 体調記録", "⚖️ 体重管理"] if user != "克己" else ["🚶 体調記録", "🩸 血圧管理", "⚖️ 体重管理"])

# --- タブ1: 体調記録 ---
with tabs[0]:
    raw_df = load_data(t_month)
    
    if user == "テト":
        # --- UI改善: テトちゃん専用フォーム ---
        st.subheader("✨ テトちゃんの今日の様子")
        
        # 写真アップ用誘導ボタン
        col_msg, col_btn = st.columns([2, 1])
        with col_msg:
            st.info("写真はGoogleフォームからアップしてね。ここに自動保存されるよ！")
        with col_btn:
            # ★ここに作成したGoogleフォームのURLを貼ってください
            form_url = "https://docs.google.com/forms/d/e/あなたのフォームID/viewform"
            st.link_button("📷 今日の写真を保存", form_url, use_container_width=True)

        with st.expander("📝 記録を入力する", expanded=True):
            with st.form("teto_form"):
                # セクション1
                st.markdown("##### 🍖 食事・水分")
                c1, c2 = st.columns(2)
                with c1:
                    food = st.select_slider("ごはんの量", options=["かなり少なめ", "少なめ", "普通", "多い", "かなり多い"], value="普通")
                with c2:
                    water = st.slider("水分補給レベル (0-10)", 0, 10, 5)
                
                st.divider()
                
                # セクション2
                st.markdown("##### 🚽 トイレ・嘔吐")
                c3, c4, c5 = st.columns(3)
                with c3:
                    poo_s = st.selectbox("うんちの状態", ["普通", "少し硬い", "かなり硬い", "柔らかい", "かなり柔らかい"])
                with c4:
                    poo_c = st.number_input("うんち回数", 0, 10, 1)
                    vomit = st.checkbox("毛玉を吐いた")
                with c5:
                    pee_c = st.number_input("おしっこ回数", 0, 10, 2)
                    brush = st.checkbox("ブラッシングした")

                st.divider()
                
                # セクション3
                st.markdown("##### 🏃 活動・元気")
                c6, c7 = st.columns(2)
                with c6:
                    genki = st.slider("総合元気度", 0, 10, 8)
                with c7:
                    active = st.slider("運動量", 0, 10, 5)
                
                memo = st.text_area("一言メモ (任意)")
                
                if st.form_submit_button("🐾 記録を保存する", use_container_width=True, type="primary"):
                    new_row = {
                        "日付": str(date.today()), "ごはんの量": food, "水分補給": water, 
                        "おしっこ回数": pee_c, "うんち回数": poo_c, "うんちの状態": poo_s, 
                        "毛玉嘔吐": vomit, "運動量": active, "ブラッシング": brush, 
                        "総合元気度": genki, "メモ": memo
                    }
                    conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.cache_data.clear(); st.success("保存完了！"); st.rerun()

        # --- 履歴と写真の表示 ---
        if not raw_df.empty:
            st.divider()
            st.subheader("📊 過去の記録と写真")
            selected_date = st.selectbox("日付を選択して振り返る", raw_df['日付'].unique()[::-1])
            
            d_col, p_col = st.columns([1, 1])
            with d_col:
                day_data = raw_df[raw_df['日付'] == selected_date].iloc[0]
                st.markdown(f"**📅 {selected_date} の記録**")
                st.write(f"🍚 ごはん: {day_data.get('ごはんの量', '-')}")
                st.write(f"💧 水分: {day_data.get('水分補給', '-')}")
                st.write(f"💩 うんち: {day_data.get('うんちの状態', '-')} ({day_data.get('うんち回数', 0)}回)")
                st.write(f"🌟 元気: {day_data.get('総合元気度', '-')}/10")
                st.write(f"📝 メモ: {day_data.get('メモ', '-')}")

            with p_col:
                # フォーム回答用シートから写真を取得
                df_photo = load_data("フォームの回答 1") # シート名を確認
                if not df_photo.empty:
                    # 日付列で照合（項目名はフォームに合わせてね）
                    photo_row = df_photo[df_photo['日付'].astype(str).str.contains(str(selected_date))]
                    if not photo_row.empty:
                        img_url = format_drive_url(photo_row.iloc[0]['今日の写真'])
                        if img_url: st.image(img_url, caption=f"{selected_date} のテト", use_container_width=True)
                    else: st.warning("この日の写真はまだありません")

    else:
        # 人間の体調管理（既存コードを維持）
        st.subheader("📝 本日の体調を入力")
        with st.form("h_form"):
            c1, c2, c3 = st.columns(3)
            with c1: wake = st.text_input("起床時間", "7:00"); sl_h = st.number_input("睡眠時間", 0.0, 24.0, 7.0)
            with c2: cond = st.slider("体調", 0, 10, 7); g = st.slider("総合実績", 0, 10, 5)
            with c3: a = st.slider("行動意欲", 0, 10, 5); f = st.slider("食生活", 0, 10, 6)
            memo_h = st.text_area("メモ")
            if st.form_submit_button("🚀 保存"):
                new_row = {"日付": str(date.today()), "睡眠時間": sl_h, "体調": cond, "総合実績": g, "行動意欲": a, "食生活": f, "メモ": memo_h}
                conn.update(spreadsheet=url, worksheet=t_month, data=pd.concat([raw_df, pd.DataFrame([new_row])], ignore_index=True))
                st.cache_data.clear(); st.rerun()

# --- タブ2: 血圧・体重 (既存の祐介PW制限などは維持) ---
# ... (以前のコードと同様の体重管理ロジック) ...

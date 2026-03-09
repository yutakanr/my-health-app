import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import altair as alt

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]},
    "テト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "teto", "weight_pw": "guest123"}
}

st.set_page_config(page_title="Health Log Pro", layout="wide")

# --- UIカスタム ---
st.markdown("""
    <style>
    div[data-testid="stCheckbox"] label p { font-weight: 600 !important; }
    div[data-testid="stForm"] { border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- 2. ログイン機能 ---
if not st.session_state.logged_in:
    st.title("🔐 Health Log Login")
    with st.columns([1,1.5,1])[1]:
        with st.container(border=True):
            user_choice = st.selectbox("👤 ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
            pw_input = st.text_input("パスワード", type="password")
            if st.button("ログイン", use_container_width=True, type="primary"):
                if user_choice != "選択してください" and pw_input == USER_DATA[user_choice]["pw"]:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_choice
                    st.rerun()
                else: st.error("パスワードが違います")
    st.stop()

# --- 3. メイン画面 ---
user = st.session_state.current_user
sheet_id = USER_DATA[user]["id"]
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
t_sheet = date.today().strftime("%Y-%m")

# ヘッダー
col_h1, col_h2 = st.columns([3, 1.5])
with col_h1:
    st.title(f"🐾 {user}ちゃんの健康管理" if user == "テト" else f"👋 {user}さんの健康管理")
with col_h2:
    st.write("")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1: st.link_button("📊 Sheet", url)
    with c_btn2: 
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

st.divider()

tabs_list = ["📝 記録・推移", "⚖️ 体重管理"]
if user == "克己": tabs_list.append("🩸 血圧管理")
sel_tab = st.tabs(tabs_list)

with sel_tab[0]:
    # データ読み込み
    try:
        df = conn.read(spreadsheet=url, worksheet=t_sheet, ttl=0)
    except:
        df = pd.DataFrame()

    # --- 修正: グラフ表示（列が存在するかチェック） ---
    if not df.empty and "ごはんの量" in df.columns:
        st.markdown("### 📈 体調トレンド")
        gdf = df.copy()
        gdf['日付'] = pd.to_datetime(gdf['日付'])
        map_10 = {"かなり多い": 8, "多い": 6, "普通": 4, "少なめ": 2, "かなり少なめ": 0, "かなり柔らかい": 8, "柔らかい": 6, "少し硬い": 2, "かなり硬い": 0}
        
        # 安全に列変換を行う
        if "ごはんの量" in gdf.columns: gdf['ごはん値'] = gdf['ごはんの量'].map(map_10).fillna(0)
        if "うんちの状態" in gdf.columns: gdf['うんち値'] = gdf['うんちの状態'].map(map_10).fillna(0)
        
        cols = ["総合元気度", "ごはん値", "うんち値", "運動量"]
        for c in cols:
            if c in gdf.columns:
                gdf[c] = pd.to_numeric(gdf[c], errors='coerce').fillna(0)
        
        gdf = gdf.sort_values('日付')
        base = alt.Chart(gdf).encode(x=alt.X('日付:T', axis=alt.Axis(format='%m/%d')))
        line1 = base.mark_line(strokeWidth=4, color='#FF69B4').encode(y='総合元気度:Q')
        line2 = base.mark_line(color='#32CD32').encode(y='ごはん値:Q')
        line3 = base.mark_line(color='#FFA500').encode(y='うんち値:Q')
        line4 = base.mark_line(color='#00BFFF').encode(y='運動量:Q')
        st.altair_chart(line1 + line2 + line3 + line4, use_container_width=True)
        st.write("💗元気度  💚ごはん  🧡うんち  💙運動量")
    else:
        st.info("まだ今月のデータがありません。下のフォームから最初の記録を入力してね！")

    # 入力フォーム
    with st.form("input_form"):
        st.markdown("### ✍️ 本日の体調を入力")
        photo_name = ""
        if user == "テト":
            uploaded_file = st.file_uploader("📸 今日のベストショット", type=['jpg', 'jpeg', 'png'])
            if uploaded_file:
                st.image(uploaded_file, width=250)
                photo_name = uploaded_file.name
            st.divider()

        c1, c2, c3 = st.columns(3)
        if user == "テト":
            with c1:
                st.markdown("**🍴 食事・おしっこ**")
                food_val = st.selectbox("ごはんの量", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
                water_val = st.slider("水分補給", 1, 10, 5)
                pee_count = st.slider("おしっこ回数", 0, 10, 2)
                vomit = st.checkbox("毛玉・嘔吐あり")
            with c2:
                st.markdown("**💩 排泄・睡眠**")
                poo_count = st.number_input("うんち回数", 0, 10, 1)
                poo_state = st.selectbox("うんちの状態", ["かなり硬い", "少し硬い", "普通", "柔らかい", "かなり柔らかい"], index=2)
                sleep_cat = st.selectbox("睡眠時間", ["かなり寝た", "結構寝た", "普通に寝た", "あまり寝てない", "ほとんど寝てない"], index=2)
            with c3:
                st.markdown("**🏃 元気度・ケア**")
                total_genki = st.slider("総合元気度", 1, 10, 8)
                activity = st.slider("運動量", 1, 10, 5)
                brushing = st.checkbox("ブラッシング/ケア済")
        else:
            with c1: sleep_cat = st.selectbox("睡眠状況", ["かなり寝た", "結構寝た", "普通に寝た", "あまり寝てない", "ほとんど寝てない"], index=2)
            with c2: total_genki = st.slider("総合実績", 1, 10, 5)
            with c3: activity = st.slider("行動意欲", 1, 10, 5)
            food_val, water_val, pee_count, vomit, poo_count, poo_state, brushing = "普通", 5, 0, False, 0, "普通", False

        st.markdown("---")
        memo = st.text_area("🗒️ メモ・日記", height=100)
        
        if st.form_submit_button("🚀 記録を保存", use_container_width=True, type="primary"):
            new_row = {
                "日付": str(date.today()), "ごはんの量": food_val, "水分補給": water_val, "おしっこ回数": pee_count,
                "うんち回数": poo_count, "うんちの状態": poo_state, "毛玉嘔吐": vomit, "睡眠時間": sleep_cat, 
                "運動量": activity, "ブラッシング": brushing, "写真名": photo_name, "総合元気度": total_genki, "メモ": memo
            }
            # 空のデータフレームでも結合できるように調整
            combined_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(spreadsheet=url, worksheet=t_sheet, data=combined_df)
            st.success("保存しました！")
            st.rerun()

    if not df.empty:
        st.markdown("### 📋 履歴一覧")
        st.dataframe(df.sort_values("日付", ascending=False), use_container_width=True)

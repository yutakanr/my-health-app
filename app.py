import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime, timedelta
import altair as alt

# --- 1. ユーザーデータ設定 ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke", "weight_pw": st.secrets["passwords"]["user_a_weight"]},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi", "weight_pw": st.secrets["passwords"]["user_b_weight"]},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko", "weight_pw": st.secrets["passwords"]["user_c_weight"]},
    "テト": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "teto", "weight_pw": "guest123"}
}

st.set_page_config(page_title="Health Log Pro", layout="wide")

# UIデザインの強制修正
st.markdown("""
    <style>
    .stApp { color: #31333F; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 5px; color: #31333F !important; }
    .stTabs [aria-selected="true"] { background-color: #2196f3 !important; color: white !important; }
    div[data-testid="stForm"] { background-color: #ffffff; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    label { color: #31333F !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- 2. ログイン機能 ---
if not st.session_state.logged_in:
    st.title("🔐 Health Log Login")
    with st.columns([1,2,1])[1]:
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
c_h1, c_h2, c_h3 = st.columns([2, 2, 1])
with c_h1: st.subheader(f"🐾 こんにちは、{user}ちゃん" if user == "テト" else f"👋 こんにちは、{user}さん")
with c_h2: st.link_button("📊 Googleスプレッドシートを開く", url, use_container_width=True)
with c_h3: 
    if st.button("🚪 ログアウト", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

st.divider()
tabs_list = ["📝 記録・履歴", "⚖️ 体重管理"]
if user == "克己": tabs_list.append("🩸 血圧管理")
sel_tab = st.tabs(tabs_list)

with sel_tab[0]:
    try:
        df = conn.read(spreadsheet=url, worksheet=t_sheet, ttl=0)
    except:
        df = pd.DataFrame()

    # --- グラフ表示（表の上に配置） ---
    if not df.empty:
        st.markdown("### 📈 最新の体調推移 (1日毎)")
        gdf = df.copy()
        gdf['日付'] = pd.to_datetime(gdf['日付'])
        
        # 5段階→10段階変換ロジック
        map_10 = {
            "かなり多い": 8, "多い": 6, "普通": 4, "少なめ": 2, "かなり少なめ": 0,
            "かなり柔らかい": 8, "柔らかい": 6, "普通": 4, "少し硬い": 2, "かなり硬い": 0
        }
        
        gdf['ごはん値'] = gdf['ごはんの量'].map(map_10).fillna(0)
        gdf['うんち値'] = gdf['うんちの状態'].map(map_10).fillna(0)
        
        cols = ["総合元気度", "ごはん値", "うんち値", "運動量"]
        for c in cols: gdf[c] = pd.to_numeric(gdf[c], errors='coerce').fillna(0)
        gdf = gdf.sort_values('日付')

        base = alt.Chart(gdf).encode(x=alt.X('日付:T', axis=alt.Axis(format='%m/%d')))
        
        line1 = base.mark_line(strokeWidth=4, color='#FF69B4').encode(y='総合元気度:Q') # ピンク太線
        line2 = base.mark_line(color='#32CD32').encode(y='ごはん値:Q') # 黄緑
        line3 = base.mark_line(color='#FFA500').encode(y='うんち値:Q') # オレンジ
        line4 = base.mark_line(color='#00BFFF').encode(y='運動量:Q') # 水色

        st.altair_chart(line1 + line2 + line3 + line4, use_container_width=True)
        st.markdown("<span style='color:#FF69B4'>● 総合元気度(太)</span> <span style='color:#32CD32'>● ごはん</span> <span style='color:#FFA500'>● うんち(状態)</span> <span style='color:#00BFFF'>● 運動量</span>", unsafe_allow_html=True)

    # --- 入力フォーム ---
    with st.form("input_form"):
        st.markdown("### 📝 今日の記録を入力")
        
        photo_name = ""
        if user == "テト":
            st.markdown("📸 **今日のベストショット**")
            uploaded_file = st.file_uploader("写真を選択", type=['jpg', 'jpeg', 'png'])
            if uploaded_file:
                st.image(uploaded_file, width=300)
                photo_name = uploaded_file.name

        c1, c2, c3 = st.columns(3)
        if user == "テト":
            with c1:
                food_val = st.selectbox("ごはんの量", ["かなり多い", "多い", "普通", "少なめ", "かなり少なめ"], index=2)
                water_val = st.slider("水分補給", 1, 10, 5)
                pee_count = st.slider("おしっこ回数", 0, 10, 2)
                vomit = st.checkbox("毛玉・嘔吐あり")
            with c2:
                poo_count = st.number_input("うんち回数", 0, 10, 1)
                poo_state = st.selectbox("うんちの状態", ["かなり硬い", "少し硬い", "普通", "柔らかい", "かなり柔らかい"], index=2)
                sleep_cat = st.selectbox("睡眠時間", ["かなり寝た", "結構寝た", "普通に寝た", "あまり寝てない", "ほとんど寝てない"], index=2)
            with c3:
                total_genki = st.slider("総合元気度", 1, 10, 8)
                activity = st.slider("運動量", 1, 10, 5)
                brushing = st.checkbox("ブラッシング/ケア済")
        else:
            with c1:
                sleep_cat = st.selectbox("睡眠状況", ["かなり寝た", "結構寝た", "普通に寝た", "あまり寝てない", "ほとんど寝てない"], index=2)
            with c2:
                total_genki = st.slider("総合実績", 1, 10, 5)
                activity = st.slider("行動意欲", 1, 10, 5)
            with c3:
                food_val, water_val, pee_count, vomit, poo_count, poo_state, brushing = "普通", 5, 0, False, 0, "普通", False

        st.markdown("---")
        memo = st.text_area("🗒️ メモ・日記（今日の様子や気づいたこと）", height=150)
        
        if st.form_submit_button("🚀 記録を保存する", use_container_width=True, type="primary"):
            # 【重要】ご指定通り「写真名」と「メモ」の間に「総合元気度」を配置
            new_row = {
                "日付": str(date.today()), 
                "ごはんの量": food_val, "水分補給": water_val, "おしっこ回数": pee_count,
                "うんち回数": poo_count, "うんちの状態": poo_state, "毛玉嘔吐": vomit,
                "睡眠時間": sleep_cat, "運動量": activity, "ブラッシング": brushing, 
                "写真名": photo_name, 
                "総合元気度": total_genki, 
                "メモ": memo
            }
            conn.update(spreadsheet=url, worksheet=t_sheet, data=pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("保存したよ！✨")
            st.rerun()

    st.divider()
    st.markdown("### 📋 履歴一覧")
    if not df.empty:
        st.data_editor(df, num_rows="dynamic", use_container_width=True)

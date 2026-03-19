import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, timedelta
import altair as alt

# --- 1. 設定 & ログイン ---
USER_DATA = {
    "祐介": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "克己": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "典子": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"},
    "テト": {"id": "1gHZ51t9qMDip_Gk_EjPH14Vke4BhbQEuf2ukZC3MxkQ", "pw": "teto"} 
}

st.set_page_config(page_title="Health Log Pro", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# カスタムCSS
st.markdown("""
    <style>
    div.stButton > button:has(div p:contains("Logout")) {
        background-color: #FFD700 !important;
        color: black !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "edit_target" not in st.session_state: st.session_state.edit_target = None

if not st.session_state.logged_in:
    st.title("🔐 Login")
    u_choice = st.selectbox("ユーザーを選択", ["選択してください"] + list(USER_DATA.keys()))
    p_input = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if u_choice != "選択してください" and p_input == USER_DATA[u_choice]["pw"]:
            st.session_state.logged_in = True
            st.session_state.current_user = u_choice
            st.rerun()
    st.stop()

# --- 2. 共通ロジック ---
user = st.session_state.current_user
url = f"https://docs.google.com/spreadsheets/d/{USER_DATA[user]['id']}/edit#gid=0"
cols_order = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "食生活", "行動力", "行動意欲", "総合実績", "メモ"]

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if df is not None and not df.empty:
            df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
            return df.sort_values(['日付']).drop_duplicates(subset=['日付'], keep='last')
        return pd.DataFrame(columns=cols_order)
    except: return pd.DataFrame(columns=cols_order)

def update_sheet(sheet_name, df):
    conn.update(spreadsheet=url, worksheet=sheet_name, data=df.fillna(""))
    st.cache_data.clear()

# --- 3. UI上部 ---
st.markdown(f"### {user}の体調管理画面")
c_out, c_month, c_db, c_spacer = st.columns([0.8, 1.2, 1.8, 5])
with c_out:
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()
with c_month:
    today = date.today()
    m_opts = [(today.replace(day=1) - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
    sel_month = st.selectbox("月選択", m_opts, label_visibility="collapsed")
with c_db:
    st.link_button("📊 DBアクセス", url, use_container_width=True)

# --- 4. メイン ---
tabs = st.tabs(["🚶 体調記録", "⚖️ 体重"] + (["🩸 血圧"] if user == "克己" else []))

with tabs[0]:
    df_main = load_data(sel_month)
    
    # 編集用初期値のセット
    init_data = {"起床時間":7, "就寝時間":23, "睡眠時間":7.0, "寝つき":7, "寝起き":7, "体調":7, "食生活":6, "行動力":5, "行動意欲":5, "総合実績":5, "メモ":""}
    if st.session_state.edit_target:
        row = df_main[df_main["日付"] == st.session_state.edit_target].iloc[0]
        for k in init_data.keys():
            try:
                if k in ["起床時間", "就寝時間"]: init_data[k] = int(row[k].split(":")[0])
                else: init_data[k] = row[k]
            except: pass

    # 入力フォーム
    st.subheader("🖋 記録を入力・編集" if st.session_state.edit_target else "🖋 今日の記録")
    with st.form("input_form"):
        col_l, col_r = st.columns(2)
        with col_l:
            wake_t = st.number_input("起床時間", 0, 23, init_data["起床時間"])
            sleep_t = st.number_input("就寝時間", 0, 23, init_data["就寝時間"])
            slp_dur = st.number_input("睡眠時間合計", 0.0, 24.0, float(init_data["睡眠時間"]), 0.5)
            s_q1 = st.slider("寝つき", 0, 10, int(init_data["寝つき"]))
            s_q2 = st.slider("寝起き", 0, 10, int(init_data["寝起き"]))
        with col_r:
            cond = st.slider("体調", 0, 10, int(init_data["体調"]))
            diet = st.slider("食生活", 0, 10, int(init_data["食生活"]))
            act_p = st.slider("行動力", 0, 10, int(init_data["行動力"]))
            act_w = st.slider("行動意欲", 0, 10, int(init_data["行動意欲"]))
        perf = st.slider("総合実績", 0, 10, int(init_data["総合実績"]))
        memo = st.text_area("メモ", init_data["メモ"])
        
        btn_label = "修正を保存" if st.session_state.edit_target else "記録を保存"
        if st.form_submit_button(btn_label, use_container_width=True):
            target_date = st.session_state.edit_target if st.session_state.edit_target else str(date.today())
            new_row = {"日付": target_date, "起床時間": f"{wake_t}:00", "就寝時間": f"{sleep_t}:00", "睡眠時間": slp_dur, "寝つき": s_q1, "寝起き": s_q2, "体調": cond, "食生活": diet, "行動力": act_p, "行動意欲": act_w, "総合実績": perf, "メモ": memo}
            
            # 保存処理
            if not df_main.empty and target_date in df_main["日付"].values:
                df_main.loc[df_main["日付"] == target_date, list(new_row.keys())] = list(new_row.values())
            else:
                df_main = pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True)
            
            update_sheet(sel_month, df_main)
            st.session_state.edit_target = None
            st.rerun()

    if not df_main.empty:
        # 📈 トレンド
        st.subheader("📈 トレンド")
        plot_items = ["総合実績", "食生活", "睡眠時間", "行動力"]
        plot_df = df_main.copy()
        for c in plot_items: plot_df[c] = pd.to_numeric(plot_df[c], errors='coerce')
        m_df = plot_df.melt(id_vars=['日付'], value_vars=[c for c in plot_items if c in plot_df.columns]).dropna()
        st.altair_chart(alt.Chart(m_df).mark_line(point=True).encode(x='日付:N', y='value:Q', color='variable:N').properties(height=300), use_container_width=True)

        # 📊 週次サマリー
        st.subheader("📊 直近7日間の平均")
        recent_df = plot_df[pd.to_datetime(plot_df["日付"]) > (pd.Timestamp.now() - pd.Timedelta(days=7))]
        if not recent_df.empty:
            avg_cols = st.columns(4)
            for i, item in enumerate(plot_items):
                avg_val = recent_df[item].mean()
                avg_cols[i].metric(item, f"{avg_val:.1f}")

# --- 5. 履歴・編集・削除エリア ---
st.divider()
if not df_main.empty:
    st.subheader(f"📋 {sel_month} の履歴")
    # 削除用ダイアログ
    if "delete_id" in st.session_state:
        st.warning(f"⚠️ {st.session_state.delete_id} のデータを削除しますか？")
        c1, c2 = st.columns(2)
        if c1.button("はい、削除します"):
            df_main = df_main[df_main["日付"] != st.session_state.delete_id]
            update_sheet(sel_month, df_main)
            del st.session_state.delete_id; st.rerun()
        if c2.button("キャンセル"): del st.session_state.delete_id; st.rerun()

    # 操作ボタン付きの表
    for idx, row in df_main.sort_values("日付", ascending=False).iterrows():
        with st.expander(f"📅 {row['日付']} - 体調:{row['体調']} / 実績:{row['総合実績']}"):
            col_a, col_b, col_c = st.columns([4, 1, 1])
            col_a.write(row.to_frame().T[cols_order])
            if col_b.button("📝 編集", key=f"ed_{row['日付']}"):
                st.session_state.edit_target = row['日付']; st.rerun()
            if col_c.button("🗑️ 削除", key=f"del_{row['日付']}"):
                st.session_state.delete_id = row['日付']; st.rerun()

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
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

# ボタンの色のカスタムCSS
st.markdown("""
    <style>
    div.stButton > button:has(div p:contains("Logout")) {
        background-color: #FFD700 !important; color: black !important; font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "edit_target" not in st.session_state: st.session_state.edit_target = None
if "delete_target" not in st.session_state: st.session_state.delete_target = None

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
cols_order = ["日付", "起床時間", "就寝時間", "睡眠時間", "寝つき", "寝起き", "体調", "食生活", "行動意欲", "行動力", "総合実績", "メモ"]

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=url, worksheet=sheet_name, ttl=0)
        if df is not None and not df.empty:
            df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
            return df.sort_values(['日付'], ascending=False).drop_duplicates(subset=['日付'], keep='last')
        return pd.DataFrame(columns=cols_order)
    except: return pd.DataFrame(columns=cols_order)

def update_sheet(sheet_name, df):
    conn.update(spreadsheet=url, worksheet=sheet_name, data=df.fillna(""))
    st.cache_data.clear()

# --- 3. UI上部 ---
st.markdown(f"### {user}の体調管理画面")
c_out, c_month, c_db, _ = st.columns([0.8, 1.2, 1.8, 5])
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
    
    # 初期値設定
    init = {"w_h":7, "w_m":0, "s_h":23, "s_m":0, "dur":7.0, "s1":7, "s2":7, "c":7, "d":6, "aw":5, "ap":5, "perf":5, "memo":""}
    if st.session_state.edit_target:
        row = df_main[df_main["日付"] == st.session_state.edit_target].iloc[0]
        try:
            init["w_h"], init["w_m"] = map(int, str(row["起床時間"]).split(":"))
            init["s_h"], init["s_m"] = map(int, str(row["就寝時間"]).split(":"))
            init["dur"], init["s1"], init["s2"], init["c"], init["d"], init["aw"], init["ap"], init["perf"], init["memo"] = row["睡眠時間"], row["寝つき"], row["寝起き"], row["体調"], row["食生活"], row["行動意欲"], row["行動力"], row["総合実績"], row["メモ"]
        except: pass

    # 入力フォーム
    with st.form("main_form"):
        st.subheader("📝 編集モード" if st.session_state.edit_target else "📝 今日の記録")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**【睡眠】**")
            # 分単位入力のためのセレクトボックス
            cw1, cw2 = st.columns(2)
            w_h = cw1.selectbox("起床（時）", list(range(24)), index=init["w_h"])
            w_m = cw2.selectbox("起床（分）", [f"{i:02d}" for i in range(60)], index=init["w_m"])
            cs1, cs2 = st.columns(2)
            s_h = cs1.selectbox("就寝（時）", list(range(24)), index=init["s_h"])
            s_m = cs2.selectbox("就寝（分）", [f"{i:02d}" for i in range(60)], index=init["s_m"])
            
            dur = st.number_input("睡眠時間合計", 0.0, 24.0, float(init["dur"]), 0.1)
            s1 = st.slider("寝つき", 0, 10, int(init["s1"]))
            s2 = st.slider("寝起き", 0, 10, int(init["s2"]))
        with c2:
            st.markdown("**【体調・行動】**")
            c = st.slider("体調", 0, 10, int(init["c"]))
            d = st.slider("食生活", 0, 10, int(init["d"]))
            aw = st.slider("行動意欲", 0, 10, int(init["aw"]))
            ap = st.slider("行動力", 0, 10, int(init["ap"]))
        
        perf = st.slider("総合実績", 0, 10, int(init["perf"]))
        memo = st.text_area("メモ", init["memo"])
        
        # フォームの送信ボタン（必須）
        save_label = "修正を保存する" if st.session_state.edit_target else "記録を保存する"
        if st.form_submit_button(save_label, use_container_width=True):
            t_date = st.session_state.edit_target if st.session_state.edit_target else str(date.today())
            new_row = {
                "日付": t_date, "起床時間": f"{w_h}:{w_m}", "就寝時間": f"{s_h}:{s_m}",
                "睡眠時間": dur, "寝つき": s1, "寝起き": s2, "体調": c, "食生活": d,
                "行動意欲": aw, "行動力": ap, "総合実績": perf, "メモ": memo
            }
            if not df_main.empty and t_date in df_main["日付"].values:
                df_main.loc[df_main["日付"] == t_date, list(new_row.keys())] = list(new_row.values())
            else:
                df_main = pd.concat([df_main, pd.DataFrame([new_row])], ignore_index=True)
            
            update_sheet(sel_month, df_main)
            st.session_state.edit_target = None
            st.rerun()

    # 履歴操作パネル
    if not df_main.empty:
        st.divider()
        st.subheader(f"📋 {sel_month} の履歴管理")
        
        if st.session_state.delete_target:
            st.error(f"⚠️ {st.session_state.delete_target} のデータを削除しますか？")
            dc1, dc2 = st.columns(2)
            if dc1.button("実行：削除", use_container_width=True):
                df_main = df_main[df_main["日付"] != st.session_state.delete_target]
                update_sheet(sel_month, df_main)
                st.session_state.delete_target = None; st.rerun()
            if dc2.button("キャンセル", use_container_width=True):
                st.session_state.delete_target = None; st.rerun()

        op1, op2, _ = st.columns([3, 3, 4])
        target_dates = df_main["日付"].tolist()
        with op1:
            e_date = st.selectbox("編集対象を選択", ["選択なし"] + target_dates)
            if st.button("📝 編集を開始する", use_container_width=True):
                if e_date != "選択なし":
                    st.session_state.edit_target = e_date; st.rerun()
        with op2:
            d_date = st.selectbox("削除対象を選択", ["選択なし"] + target_dates)
            if st.button("🗑️ 削除を準備する", use_container_width=True):
                if d_date != "選択なし":
                    st.session_state.delete_target = d_date; st.rerun()

        # 月ごとのフラットな表を表示
        st.dataframe(df_main[cols_order].sort_values("日付", ascending=False), use_container_width=True)

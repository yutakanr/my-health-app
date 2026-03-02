import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 設定（基本PWはコードに直接、体重PWはSecretsから読み込み） ---
USER_DATA = {
    "ユーザーA": {
        "id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", 
        "pw": "yusuke", # 基本ログイン
        "weight_pw": st.secrets["passwords"]["user_a_weight"] # 体重専用
        
    },
    "ユーザーB": {
        "id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", 
        "pw": "katsumi", 
        "weight_pw": st.secrets["passwords"]["user_b_weight"]
    },
    "ユーザーC": {
        "id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", 
        "pw": "noriko", 
        "weight_pw": st.secrets["passwords"]["user_c_weight"]
    }
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- スタイル設定 ---
st.markdown("""
    <style>
    div[data-baseweb="select"] { font-size: 20px !important; }
    label[data-testid="stWidgetLabel"] p { font-size: 22px !important; font-weight: bold; }
    .stButton button { width: 100%; font-weight: bold; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"

st.title("🛡️ 生活リズム・体調管理")

# 1. ユーザー選択
_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    selected_user = st.selectbox("👤 ユーザーを選んでね", ["選択してください"] + list(USER_DATA.keys()))

if selected_user != "選択してください":
    # 2. 基本ログイン認証
    _, pw_col, _ = st.columns([1, 2, 1])
    with pw_col:
        password = st.text_input(f"{selected_user} の基本パスワードを入力", type="password")
    
    if password == USER_DATA[selected_user]["pw"]:
        sheet_id = USER_DATA[selected_user]["id"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
        current_month = date.today().strftime("%Y-%m")
        target_sheet = f"{current_month}"

        # 画面切り替えボタン
        st.divider()
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📝 日報入力・履歴を表示"):
                st.session_state.view_mode = "main"
        with col_btn2:
            if st.button("⚖️ 体重管理画面を開く"):
                st.session_state.view_mode = "weight"

        # データの読み込み
        try:
            data = conn.read(spreadsheet=url, worksheet=target_sheet, ttl=0)
        except Exception:
            columns = ["日付", "体重", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
            data = pd.DataFrame(columns=columns)
            conn.update(spreadsheet=url, worksheet=target_sheet, data=data)

        # --- 【体重管理画面】 ---
        if st.session_state.view_mode == "weight":
            st.header("⚖️ 体重モニタリング（要専用認証）")
            _, weight_pw_col, _ = st.columns([1, 2, 1])
            with weight_pw_col:
                w_password = st.text_input(f"{selected_user} の体重専用パスワードを入力", type="password")
            
            if w_password == USER_DATA[selected_user]["weight_pw"]:
                st.success("認証成功！")
                if not data.empty:
                    graph_data = data.copy()
                    graph_data["体重"] = pd.to_numeric(graph_data["体重"], errors='coerce')
                    weight_chart = {
                        "mark": {"type": "line", "point": {"size": 80, "color": "#FFA500"}, "color": "#FFA500", "tooltip": True},
                        "encoding": {
                            "x": {"field": "日付", "type": "nominal", "axis": {"labelAngle": -45}},
                            "y": {"field": "体重", "type": "quantitative", "scale": {"zero": False}, "title": "体重 (kg)"},
                            "tooltip": [{"field": "日付"}, {"field": "体重"}]
                        },
                        "width": "container", "height": 400
                    }
                    st.vega_lite_chart(graph_data, weight_chart, use_container_width=True)
                    st.dataframe(graph_data[["日付", "体重"]].sort_index(ascending=False), use_container_width=True)
            elif w_password != "":
                st.error("体重専用パスワードが違うよ！")

        # --- 【メイン日報画面】 ---
        else:
            st.header("📝 日報入力・グラフ")
            with st.form("input_form"):
                col_time1, col_time2, col_weight = st.columns(3)
                with col_time1: bedtime = st.text_input("昨夜の就寝時間", "22:00")
                with col_time2: wakeup_time = st.text_input("今朝の起床時間", "06:30")
                with col_weight: weight = st.slider("今の体重 (kg)", 40.0, 120.0, 65.0, 0.1)

                c1, c2, c3 = st.columns(3)
                with c1:
                    wake_up_score = st.slider("寝起きの良さ", 1, 10, 5); mood = st.slider("気分", 1, 10, 5)
                with c2:
                    sleep_quality = st.slider("寝つきの良さ", 1, 10, 5); condition = st.slider("体の調子", 1, 10, 5)
                with c3:
                    motivation = st.slider("行動意欲", 1, 10, 5); total_performance = st.slider("総合実績", 1, 10, 5)
                
                col_extra1, col_extra2 = st.columns(2)
                with col_extra1: diet_score = st.slider("食生活", 1, 10, 5)
                with col_extra2: sleep_hours = st.slider("睡眠時間", 0.0, 12.0, 7.5, 0.5)
                memo = st.text_area("メモ")
                submit = st.form_submit_button("保存する")

            if submit:
                new_row = pd.DataFrame([{"日付": str(date.today()), "体重": weight, "食生活": diet_score, "就寝時間": bedtime, "起床時間": wakeup_time, "寝起き": wake_up_score, "寝つき": sleep_quality, "行動意欲": motivation, "気分": mood, "体調": condition, "総合実績": total_performance, "睡眠時間": sleep_hours, "メモ": memo}])
                data = pd.concat([data, new_row], ignore_index=True)
                conn.update(spreadsheet=url, worksheet=target_sheet, data=data)
                st.success("保存完了！")
                st.rerun()

            if not data.empty:
                st.divider()
                st.subheader("📊 履歴 (体重以外)")
                header_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1])
                headers = ["日付", "食生活", "就寝", "起床", "寝起", "寝つ", "意欲", "気分", "体調", "実績", "メモ", "削除"]
                for col, h in zip(header_cols, headers): col.write(f"**{h}**")

                for i, row in data.sort_index(ascending=False).iterrows():
                    row_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1])
                    for idx, val in enumerate(["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "メモ"]):
                        row_cols[idx].write(row.get(val, ""))
                    if row_cols[11].button("🗑️", key=f"del_{i}"):
                        updated_data = data.drop(i)
                        conn.update(spreadsheet=url, worksheet=target_sheet, data=updated_data)
                        st.rerun()

    elif password != "":
        st.error("基本パスワードが違うよ！")
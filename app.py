import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 設定 ---
USER_DATA = {
    "ユーザーA": "https://docs.google.com/spreadsheets/d/1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE/edit#gid=0",
    "ユーザーB": "https://docs.google.com/spreadsheets/d/1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50/edit#gid=0",
    "ユーザーC": "https://docs.google.com/spreadsheets/d/17LGbxNTbP4PO5N3dnTWsC-OTJB88u_dRBG-k8JOj0aw/edit#gid=0"
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 生活リズム・体調管理")

# 1. ユーザー選択
selected_user = st.selectbox("名前を選んでね", ["選択してください"] + list(USER_DATA.keys()))

if selected_user != "選択してください":
    url = USER_DATA[selected_user]
    current_month = date.today().strftime("%Y-%m")
    target_sheet = f"{selected_user}_{current_month}"

    # --- スプレッドシートを開くボタンを追加 ---
    st.link_button(f"📊 {selected_user} のスプレッドシートを開く", url)

    # サイドバー：予定表
    with st.sidebar:
        st.header("⏰ 予定表")
        schedule = {"06:30": "起床・準備", "07:00": "外出", "13:00": "IT学習", "17:00": "筋トレ", "22:00": "就寝"}
        for t, task in schedule.items():
            st.write(f"**{t}** : {task}")

    # メイン：入力フォーム
    with st.form("input_form"):
        col_time1, col_time2 = st.columns(2)
        with col_time1: bedtime = st.text_input("昨夜の就寝時間", "22:00")
        with col_time2: wakeup_time = st.text_input("今朝の起床時間", "06:30")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            wake_up_score = st.slider("寝起きの良さ", 1, 10, 5)
            mood = st.slider("気分", 1, 10, 5)
        with c2:
            sleep_quality = st.slider("寝つきの良さ", 1, 10, 5)
            condition = st.slider("体の調子", 1, 10, 5)
        with c3:
            motivation = st.slider("行動意欲", 1, 10, 5)
            total_performance = st.slider("総合実績", 1, 10, 5)
        
        col_extra1, col_extra2 = st.columns(2)
        with col_extra1:
            diet_score = st.slider("食生活（栄養・量など）", 1, 10, 5)
        with col_extra2:
            sleep_hours = st.slider("睡眠時間", 0.0, 12.0, 7.5, 0.5)
            
        memo = st.text_area("メモ（食べたものや気づいたことなど）")
        submit = st.form_submit_button("保存する")

    # --- シートの読み込み/作成 ---
    try:
        data = conn.read(spreadsheet=url, worksheet=target_sheet, ttl=0)
    except Exception:
        st.info(f"✨ 新しい月のシート「{target_sheet}」を作成するね！")
        columns = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
        data = pd.DataFrame(columns=columns)
        conn.update(spreadsheet=url, worksheet=target_sheet, data=data)

    if submit:
        new_row = pd.DataFrame([{
            "日付": str(date.today()), 
            "食生活": diet_score,
            "就寝時間": bedtime, 
            "起床時間": wakeup_time, 
            "寝起き": wake_up_score, 
            "寝つき": sleep_quality, 
            "行動意欲": motivation, 
            "気分": mood, 
            "体調": condition, 
            "総合実績": total_performance, 
            "睡眠時間": sleep_hours, 
            "メモ": memo
        }])
        data = pd.concat([data, new_row], ignore_index=True)
        conn.update(spreadsheet=url, worksheet=target_sheet, data=data)
        st.success("保存したよ！")
        st.rerun()

    # --- 履歴とグラフ ---
    if not data.empty:
        st.divider()
        st.subheader(f"📊 {current_month} の振り返り")
        
        graph_data = data.copy()
        target_cols = ["総合実績", "行動意欲", "睡眠時間", "食生活"]
        for col in target_cols:
            graph_data[col] = pd.to_numeric(graph_data[col], errors='coerce')

        melted_data = graph_data.melt(
            id_vars=["日付", "メモ"], 
            value_vars=target_cols,
            var_name="項目", 
            value_name="スコア"
        )

        chart = {
            "mark": {"type": "line", "point": True, "tooltip": True},
            "encoding": {
                "x": {"field": "日付", "type": "nominal", "axis": {"labelAngle": -45}},
                "y": {
                    "field": "スコア", 
                    "type": "quantitative", 
                    "scale": {"domain": [0, 10]},
                    "axis": {"tickCount": 11, "title": "スコア / 時間"}
                },
                "color": {"field": "項目", "type": "nominal", "scale": {"range": ["#ff4b4b", "#00d4ff", "#1f77b4", "#50C878"]}},
                "tooltip": [
                    {"field": "日付", "type": "nominal"},
                    {"field": "項目", "type": "nominal"},
                    {"field": "スコア", "type": "quantitative"},
                    {"field": "メモ", "type": "nominal"}
                ]
            },
            "width": "container",
            "height": 450,
            "config": {
                "selection": {"manual_zoom": {"type": "interval", "bind": "scales", "zoom": False, "translate": False}}
            }
        }
        
        st.vega_lite_chart(melted_data, chart, use_container_width=True)
        st.dataframe(data.sort_index(ascending=False))

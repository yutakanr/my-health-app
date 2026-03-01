import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- ユーザーごとのスプレッドシートIDを設定 ---
# URLの /d/ と /edit の間にある長い英数字がIDだよ
USER_DATA = {
    "ユーザーA": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE",
    "ユーザーB": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50",
    "ユーザーC": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4"
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 生活リズム・体調管理")

selected_user = st.selectbox("名前を選んでね", ["選択してください"] + list(USER_DATA.keys()))

if selected_user != "選択してください":
    # IDからURLを再構成
    sheet_id = USER_DATA[selected_user]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
    current_month = date.today().strftime("%Y-%m")
    target_sheet = f"{current_month}"

    st.link_button(f"📊 {selected_user} 専用のスプレッドシートを開く", url)

    # 入力フォーム（中身はそのまま）
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
        with col_extra1: diet_score = st.slider("食生活", 1, 10, 5)
        with col_extra2: sleep_hours = st.slider("睡眠時間", 0.0, 12.0, 7.5, 0.5)
        memo = st.text_area("メモ")
        submit = st.form_submit_button("保存する")

    # データの読み書き
    try:
        # スプレッドシートを読み込む（IDを指定）
        data = conn.read(spreadsheet=url, worksheet=target_sheet, ttl=0)
    except Exception:
        st.info(f"✨ 新しい月のシートを作成するね！")
        columns = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
        data = pd.DataFrame(columns=columns)
        conn.update(spreadsheet=url, worksheet=target_sheet, data=data)

    if submit:
        new_row = pd.DataFrame([{"日付": str(date.today()), "食生活": diet_score, "就寝時間": bedtime, "起床時間": wakeup_time, "寝起き": wake_up_score, "寝つき": sleep_quality, "行動意欲": motivation, "気分": mood, "体調": condition, "総合実績": total_performance, "睡眠時間": sleep_hours, "メモ": memo}])
        data = pd.concat([data, new_row], ignore_index=True)
        conn.update(spreadsheet=url, worksheet=target_sheet, data=data)
        st.success("保存したよ！")
        st.rerun()

    # グラフ表示
    if not data.empty:
        st.divider()
        st.subheader(f"📊 {current_month} の振り返り")
        graph_data = data.copy()
        target_cols = ["総合実績", "行動意欲", "睡眠時間", "食生活"]
        for col in target_cols:
            graph_data[col] = pd.to_numeric(graph_data[col], errors='coerce')
        melted_data = graph_data.melt(id_vars=["日付", "メモ"], value_vars=target_cols, var_name="項目", value_name="スコア")
        chart = {
            "mark": {"type": "line", "point": True, "tooltip": True},
            "encoding": {
                "x": {"field": "日付", "type": "nominal"},
                "y": {"field": "スコア", "type": "quantitative", "scale": {"domain": [0, 10]}},
                "color": {"field": "項目", "type": "nominal", "scale": {"range": ["#ff4b4b", "#00d4ff", "#1f77b4", "#50C878"]}},
                "tooltip": [{"field": "日付"}, {"field": "項目"}, {"field": "スコア"}, {"field": "メモ"}]
            },
            "width": "container", "height": 450
        }
        st.vega_lite_chart(melted_data, chart, use_container_width=True)
        st.dataframe(data.sort_index(ascending=False))

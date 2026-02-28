import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 設定 ---
USER_LIST = ["ユーザーA", "ユーザーB", "ユーザーC"] 
st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
url = "https://docs.google.com/spreadsheets/d/1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛡️ 生活リズム・体調管理")

# 1. ユーザー選択
selected_user = st.selectbox("名前を選んでね", ["選択してください"] + USER_LIST)

if selected_user != "選択してください":
    current_month = date.today().strftime("%Y-%m")
    target_sheet = f"{selected_user}_{current_month}"

    # サイドバーに予定表示
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
        
        sleep_hours = st.slider("睡眠時間", 0.0, 12.0, 7.5, 0.5)
        memo = st.text_area("メモ")
        submit = st.form_submit_button("保存する")

    # --- データの読み込みと表示 ---
    try:
        data = conn.read(spreadsheet=url, worksheet=target_sheet, ttl=0)
    except:
        data = pd.DataFrame()

    if submit:
        # (保存処理は前回と同じなので省略可ですが、一応簡略化して記載)
        new_row = pd.DataFrame([{"日付": str(date.today()), "名前": selected_user, "就寝時間": bedtime, "起床時間": wakeup_time, "寝起き": wake_up_score, "寝つき": sleep_quality, "行動意欲": motivation, "気分": mood, "体調": condition, "総合実績": total_performance, "睡眠時間": sleep_hours, "メモ": memo}])
        data = pd.concat([data, new_row], ignore_index=True)
        conn.update(spreadsheet=url, worksheet=target_sheet, data=data)
        st.success("保存したよ！")
        st.rerun() # 画面を更新してグラフを出す

    # --- 削除ボタンの追加 ---
    if not data.empty:
        st.divider()
        st.subheader("🗑️ データの修正")
        if st.button("最新の1件を削除する"):
            data = data.drop(data.index[-1]) # 最後の行を消す
            conn.update(spreadsheet=url, worksheet=target_sheet, data=data)
            st.warning("最新のデータを削除したよ。")
            st.rerun()

        # 履歴とグラフ
        st.subheader("📊 今月の振り返り")
        st.line_chart(data.set_index("日付")[["総合実績", "睡眠時間"]])
        st.dataframe(data.sort_index(ascending=False))
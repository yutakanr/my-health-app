import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 設定 ---
USER_DATA = {
    "ユーザーA": {"id": "1LwTU4uf06OgRTLkP8hWoy22Wc7Zoth_cRBxsm2jjtvE", "pw": "yusuke"},
    "ユーザーB": {"id": "1nKzeIhfBj97gQJWVCioAt_BfauQPr8CVBe49LPczr50", "pw": "katsumi"},
    "ユーザーC": {"id": "1KXm3qm_LzScn74-x0FUUoiyFotYGFfBzfv9b_jEboE4", "pw": "noriko"}
}

st.set_page_config(page_title="生活リズム・体調ログ", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- プルダウンを大きくするためのスタイル設定 ---
st.markdown("""
    <style>
    div[data-baseweb="select"] {
        font-size: 24px !important;
    }
    label[data-testid="stWidgetLabel"] p {
        font-size: 20px !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 生活リズム・体調管理")

# 1. ユーザー選択 (ラベルを大きく表示)
selected_user = st.selectbox("👤 名前を選んでね", ["選択してください"] + list(USER_DATA.keys()))

if selected_user != "選択してください":
    # 2. パスワード認証
    password = st.text_input(f"{selected_user} のパスワードを入力してね", type="password")
    
    if password == USER_DATA[selected_user]["pw"]:
        st.success(f"認証成功！こんにちは、{selected_user}さん。")
        
        sheet_id = USER_DATA[selected_user]["id"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
        current_month = date.today().strftime("%Y-%m")
        target_sheet = f"{current_month}"

        st.link_button(f"📊 {selected_user} 専用のスプレッドシートを開く", url)

        # 入力フォーム
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

        # 読み込み
        try:
            data = conn.read(spreadsheet=url, worksheet=target_sheet, ttl=0)
        except Exception:
            columns = ["日付", "食生活", "就寝時間", "起床時間", "寝起き", "寝つき", "行動意欲", "気分", "体調", "総合実績", "睡眠時間", "メモ"]
            data = pd.DataFrame(columns=columns)
            conn.update(spreadsheet=url, worksheet=target_sheet, data=data)

        if submit:
            new_row = pd.DataFrame([{"日付": str(date.today()), "食生活": diet_score, "就寝時間": bedtime, "起床時間": wakeup_time, "寝起き": wake_up_score, "寝つき": sleep_quality, "行動意欲": motivation, "気分": mood, "体調": condition, "総合実績": total_performance, "睡眠時間": sleep_hours, "メモ": memo}])
            data = pd.concat([data, new_row], ignore_index=True)
            conn.update(spreadsheet=url, worksheet=target_sheet, data=data)
            st.success("保存したよ！")
            st.rerun()

        # --- 表にゴミ箱ボタンを追加 ---
        if not data.empty:
            st.divider()
            st.subheader(f"📊 {current_month} のデータ履歴")

            # ヘッダー作成
            header_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1])
            headers = ["日付", "食生活", "就寝", "起床", "寝起", "寝つ", "意欲", "気分", "体調", "実績", "メモ", "削除"]
            for col, h in zip(header_cols, headers):
                col.write(f"**{h}**")

            # 各行のデータ表示
            for i, row in data.sort_index(ascending=False).iterrows():
                row_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1])
                row_cols[0].write(row["日付"])
                row_cols[1].write(row["食生活"])
                row_cols[2].write(row["就寝時間"])
                row_cols[3].write(row["起床時間"])
                row_cols[4].write(row["寝起き"])
                row_cols[5].write(row["寝つき"])
                row_cols[6].write(row["行動意欲"])
                row_cols[7].write(row["気分"])
                row_cols[8].write(row["体調"])
                row_cols[9].write(row["総合実績"])
                row_cols[10].write(row["メモ"])
                
                # 一番右にゴミ箱ボタン
                if row_cols[11].button("🗑️", key=f"del_{i}"):
                    updated_data = data.drop(i)
                    conn.update(spreadsheet=url, worksheet=target_sheet, data=updated_data)
                    st.warning(f"{row['日付']}のデータを削除したよ。")
                    st.rerun()

            # グラフ表示
            st.divider()
            st.subheader(f"📈 月間グラフ")
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
                    "color": {"field": "項目", "type": "nominal"},
                    "tooltip": [{"field": "日付"}, {"field": "項目"}, {"field": "スコア"}, {"field": "メモ"}]
                },
                "width": "container", "height": 400
            }
            st.vega_lite_chart(melted_data, chart, use_container_width=True)

    elif password != "":
        st.error("パスワードが違うよ！")

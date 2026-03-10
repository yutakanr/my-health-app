# --- 4. メイングラフ (0-10固定) ---
if not df_clean.empty:
    st.subheader("📈 トレンド確認")
    gdf = df_clean.copy()
    
    if user == "テト":
        target_cols = ["総合元気度", "水分補給", "運動量"]
    else:
        target_cols = ["行動意欲", "食生活", "睡眠時間"]
    
    existing_cols = [c for c in target_cols if c in gdf.columns]
    
    if existing_cols:
        melted_df = gdf.melt(id_vars=['日付'], value_vars=existing_cols, var_name='項目', value_name='数値')
        # ↓ ここを修正：domain_max を 10 に直接指定
        chart = alt.Chart(melted_df).mark_line(point=True).encode(
            x=alt.X('日付:N', title='日付'), 
            y=alt.Y('数値:Q', scale=alt.Scale(domain=[0, 10], clamp=True), axis=alt.Axis(values=[0, 2, 4, 6, 8, 10]), title='スコア'),
            color=alt.Color('項目:N', title='凡例'), 
            tooltip=['日付', '項目', '数値']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)

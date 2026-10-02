                title="Monthly Trend — Top Reagents",
                labels={"Sales_USD": "Sales (USD)", "Reagent_Name": "Reagent"},
            )
            chart_or_info(fig)


# -------------------------
# Installed base
# -------------------------
with tab_installed:
    st.caption(
        f"2018-01-01부터 {year_end}-12-31까지 누적. 매출 0인 FOC Analyzer도 수량에 포함합니다."
    )

    model_options = sorted(
        m for m in installed_df["Device_Model"].dropna().unique().tolist() if m
    )
    selected_models = st.multiselect(
        "기기 모델",
        options=model_options,
        default=[],
        placeholder="선택 없으면 전체 모델",
        key="installed_model_filter",
    )

    ib = installed_df.copy()
    if selected_models:
        ib = ib[ib["Device_Model"].isin(selected_models)]

    snapshot = (
        ib.pivot_table(
            index="Country",
            columns="Device_Model",
            values="Device_Units",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )

    if not snapshot.empty:
        snapshot["Total"] = snapshot.sum(axis=1)
        snapshot = snapshot.sort_values("Total", ascending=False)

    st.subheader(f"Cumulative Device Units by Country — through {year_end}")
    st.dataframe(
        snapshot,
        use_container_width=True,
        column_config={
            c: st.column_config.NumberColumn(format="%,.0f")
            for c in snapshot.columns
        } if not snapshot.empty else None,
    )

    monthly_units = (
        ib.groupby(["Month", "Device_Model"], as_index=False)["Device_Units"]
        .sum()
        .sort_values("Month")
    )

    if not monthly_units.empty:
        full_months = pd.date_range(
            start=f"{START_YEAR}-01-01",
            end=end_date,
            freq="MS",
        )
        models = sorted(monthly_units["Device_Model"].dropna().unique())
        full_idx = pd.MultiIndex.from_product(
            [full_months, models], names=["Month", "Device_Model"]
        )
        cumulative = (
            monthly_units.set_index(["Month", "Device_Model"])
            .reindex(full_idx, fill_value=0)
            .reset_index()
            .sort_values(["Device_Model", "Month"])
        )
        cumulative["Cumulative_Units"] = cumulative.groupby("Device_Model")[
            "Device_Units"
        ].cumsum()

        fig = px.line(
            cumulative,
            x="Month",
            y="Cumulative_Units",
            color="Device_Model",
            title="Cumulative Analyzer Installed Base",
            labels={"Cumulative_Units": "Cumulative Units", "Device_Model": "Model"},
        )
        chart_or_info(fig)

    st.subheader("Country → Company → Model")
    company_device = (
        ib.groupby(["Country", "Company", "Device_Model"], as_index=False)
        .agg(
            Cumulative_Units=("Device_Units", "sum"),
            FOC_Units=(
                "Device_Units",
                lambda s: s[ib.loc[s.index, "Is_FOC"]].sum()
                if len(s.index) else 0
            ),
        )
        .sort_values(["Country", "Company", "Cumulative_Units"], ascending=[True, True, False])
    )
    st.dataframe(
        company_device,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Cumulative_Units": st.column_config.NumberColumn(format="%,.0f"),
            "FOC_Units": st.column_config.NumberColumn(format="%,.0f"),
        },
    )


# -------------------------
# Raw data
# -------------------------
with tab_raw:
    raw_cols = [
        "Date",
        "Country",
        "Company",
        "Department",
        "Salesperson",
        "Product_Name",
        "Product_Code",
        "Item_Group",
        "Device_Model",
        "Reagent_Name",
        "Currency",
        "FX_Rate",
        "USD_KRW_Rate",
        "Sales_USD",
        "Quantity",
        "Net_Quantity",
        "Is_FOC",
        "Is_Return",
        "Source_File",
    ]
    raw_view = period_df[raw_cols].sort_values("Date", ascending=False)

    st.dataframe(
        raw_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Sales_USD": st.column_config.NumberColumn(format="$%,.2f"),
            "FX_Rate": st.column_config.NumberColumn(format="%,.2f"),
            "USD_KRW_Rate": st.column_config.NumberColumn(format="%,.2f"),
            "Quantity": st.column_config.NumberColumn(format="%,.2f"),
            "Net_Quantity": st.column_config.NumberColumn(format="%,.2f"),
        },
    )

    csv = raw_view.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Filtered data CSV 다운로드",
        data=csv,
        file_name=f"sales_dashboard_{year_start}_{year_end}.csv",
        mime="text/csv",
    )

    with st.expander("USD 환산 / 데이터 품질 확인"):
        fx_coverage = period_df["USD_KRW_Rate"].notna().mean() if len(period_df) else 0
        unknown_country = (period_df["Country"] == "Unknown").sum()
        unmapped_product = (period_df["Item_Group"] == "Other").sum()
        st.write(f"- USD/KRW 환율 커버리지: {fx_coverage:.1%}")
        st.write(f"- 국가 미분류 행: {unknown_country:,}")
        st.write(f"- Device/Reagent 외 Other 행: {unmapped_product:,}")
        st.write(
            "- 국가/회사명이 예외적인 경우 `config/company_country_map.csv`, "
            "신규 기기명이 생기면 `config/device_model_aliases.csv`에 추가하면 됩니다."
        )

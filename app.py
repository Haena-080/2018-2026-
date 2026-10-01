import os
import glob
import re

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Africa Sales Dashboard",
    page_icon="🌍",
    layout="wide",
)


def find_column(df, *names):
    """Return the first matching column name, ignoring spaces and case."""
    normalized = {}
    for col in df.columns:
        key = re.sub(r"\s+", "", str(col)).lower()
        normalized[key] = col

    for name in names:
        key = re.sub(r"\s+", "", str(name)).lower()
        if key in normalized:
            return normalized[key]
    return None


def detect_header_row(path):
    preview = pd.read_excel(path, sheet_name=0, header=None, nrows=12)
    for idx in range(len(preview)):
        row = preview.iloc[idx].astype(str).tolist()
        joined = " | ".join(row)
        if "품명" in joined and "고객" in joined and "외화금액" in joined:
            return idx
    return 4


def normalize_country(value):
    if pd.isna(value):
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text or text.lower() == "nan":
        return ""

    upper = text.upper()
    if upper == "THE GAMBIA":
        return "Gambia"
    if upper == "GAMBIA":
        return "Gambia"
    if upper == "GHANA":
        return "Ghana"
    if upper == "BOTSWANA":
        return "Botswana"
    if upper == "RWANDA":
        return "Rwanda"
    if upper == "LIBERIA":
        return "Liberia"
    if upper in ("CAPE VERDE", "CABO VERDE"):
        return "Cape Verde"
    if upper in ("SIERRA LEONE", "SIERRALEONE"):
        return "Sierra Leone"
    if upper in ("COTE D'IVOIRE", "CÔTE D'IVOIRE", "IVORY COAST"):
        return "Côte d'Ivoire"
    return text.title()


def normalize_company(value):
    if pd.isna(value):
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text or text.lower() == "nan":
        return ""
    # Database often stores "Company; Country" in the customer column.
    return text.split(";")[0].strip()


def classify_device(item_name):
    name = re.sub(r"[\s\-_]", "", str(item_name).upper())
    if "AFIAS10" in name:
        return "AFIAS-10"
    if "AFIAS6" in name:
        return "AFIAS-6"
    if "AFIAS3" in name:
        return "AFIAS-3"
    if "AFIAS1" in name or "AFIAS" in name:
        return "AFIAS-1 / Other AFIAS"
    if "ICHROMAIII" in name or "ICHROMA3" in name:
        return "ichroma III"
    if "ICHROMAII" in name or "ICHROMA2" in name or "ICHROMA" in name:
        return "ichroma II"
    if "CHEMICHROMA" in name:
        return "Chemichroma"
    if "HEMOCHROMA" in name:
        return "Hemochroma"
    if "CBCHROMA" in name:
        return "CBChroma"
    return "Other Device"


def read_one_file(path_or_upload):
    file_name = getattr(path_or_upload, "name", os.path.basename(str(path_or_upload)))
    header_row = detect_header_row(path_or_upload)
    df = pd.read_excel(path_or_upload, sheet_name=0, header=header_row)
    df = df.dropna(how="all").copy()

    date_col = find_column(df, "마감일자/출고일자", "매출일자", "출고일자")
    customer_col = find_column(df, "고객", "거래처", "고객명", "거래처명")
    country_col = find_column(df, "수출국가", "국가", "Country")
    item_col = find_column(df, "품명", "제품명", "Product", "Item Name")
    item_code_col = find_column(df, "품번", "제품코드", "SKU", "Item Code")
    krw_col = find_column(df, "원화금액", "원화매출", "KRW Amount")
    foreign_col = find_column(df, "외화금액", "외화매출", "Foreign Amount")
    currency_col = find_column(df, "환종", "통화", "Currency")
    qty_col = find_column(df, "수량환산", "수량", "판매수량", "출고수량")
    region_col = find_column(df, "Region", "지역", "권역")
    l1_col = find_column(df, "Level 1", "Level1")
    l2_col = find_column(df, "Level 2", "Level2")
    l3_col = find_column(df, "Level 3", "Level3")
    l4_col = find_column(df, "Level 4", "Level4")
    l5_col = find_column(df, "Level 5", "Level5")

    if customer_col is None or country_col is None or item_col is None:
        raise ValueError(f"필수 컬럼(고객/수출국가/품명)을 찾을 수 없습니다: {file_name}")

    out = pd.DataFrame(index=df.index)
    out["Source File"] = file_name
    out["Date"] = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.NaT
    out["Country"] = df[country_col].apply(normalize_country)
    out["Company"] = df[customer_col].apply(normalize_company)
    out["Item"] = df[item_col].astype(str).str.strip()
    out["Item Code"] = df[item_code_col].astype(str).str.strip() if item_code_col else ""
    out["Sales KRW"] = pd.to_numeric(df[krw_col], errors="coerce").fillna(0) if krw_col else 0.0
    out["Foreign Amount"] = pd.to_numeric(df[foreign_col], errors="coerce").fillna(0) if foreign_col else 0.0
    out["Currency"] = df[currency_col].astype(str).str.strip() if currency_col else ""
    out["Region"] = df[region_col].astype(str).str.strip() if region_col else ""
    out["Quantity"] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0) if qty_col else 0.0
    out["Level 1"] = df[l1_col].astype(str).str.strip() if l1_col else ""
    out["Level 2"] = df[l2_col].astype(str).str.strip() if l2_col else ""
    out["Level 3"] = df[l3_col].astype(str).str.strip() if l3_col else ""
    out["Level 4"] = df[l4_col].astype(str).str.strip() if l4_col else ""
    out["Level 5"] = df[l5_col].astype(str).str.strip() if l5_col else ""

    # Use the actual sales/shipping date when available.
    out["Year"] = out["Date"].dt.year
    out["Month"] = out["Date"].dt.month

    # Fallback to year in filename only for rows without a valid date.
    match = re.search(r"20\d{2}", file_name)
    source_year = int(match.group()) if match else None
    if source_year is not None:
        out["Year"] = out["Year"].fillna(source_year)

    out["Year"] = pd.to_numeric(out["Year"], errors="coerce").astype("Int64")

    # Annual files sometimes contain a small number of old rows.
    # When the file is clearly a single-year DB, keep only that file year.
    if source_year is not None:
        valid_years = out["Year"].dropna()
        if len(valid_years) > 0:
            same_year_ratio = (valid_years == source_year).mean()
            if same_year_ratio >= 0.80:
                out = out[out["Year"].eq(source_year) | out["Year"].isna()].copy()
    out["Month"] = pd.to_numeric(out["Month"], errors="coerce").astype("Int64")

    out = out[(out["Country"] != "") & (out["Company"] != "")]
    return out


@st.cache_data(show_spinner=False)
def load_local_data(file_paths):
    frames = []
    errors = []
    for path in file_paths:
        try:
            frames.append(read_one_file(path))
        except Exception as exc:
            errors.append(f"{os.path.basename(path)}: {exc}")

    if not frames:
        return pd.DataFrame(), errors

    data = pd.concat(frames, ignore_index=True).reset_index(drop=True)
    return data, errors


def load_uploaded_data(uploaded_files):
    frames = []
    errors = []
    for upload in uploaded_files:
        try:
            frames.append(read_one_file(upload))
        except Exception as exc:
            errors.append(f"{upload.name}: {exc}")
    if not frames:
        return pd.DataFrame(), errors
    data = pd.concat(frames, ignore_index=True)
    return data, errors


def format_krw(value):
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"₩{value / 1_000_000_000:,.1f}B"
    if abs(value) >= 1_000_000:
        return f"₩{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"₩{value / 1_000:,.1f}K"
    return f"₩{value:,.0f}"


st.title("Africa Sales Dashboard")
st.caption("Country → Company → Product / Device analysis")

local_files = sorted(glob.glob("data/*.xlsx"))
uploaded_files = st.sidebar.file_uploader(
    "Excel DB upload (optional)",
    type=["xlsx"],
    accept_multiple_files=True,
)

if uploaded_files:
    df, load_errors = load_uploaded_data(uploaded_files)
    source_label = "Uploaded files"
else:
    df, load_errors = load_local_data(tuple(local_files))
    source_label = "GitHub data/ folder"

if load_errors:
    with st.expander("Files that could not be loaded"):
        for error in load_errors:
            st.write(error)

if df.empty:
    st.warning("No usable Excel data was found. Add .xlsx files to the data/ folder or upload them from the sidebar.")
    st.stop()

# Default to Africa because these files contain global sales as well.
st.sidebar.markdown("### Filters")
africa_only = st.sidebar.checkbox("Africa region only", value=True)

base_df = df.copy()
if africa_only and "Region" in base_df.columns:
    africa_mask = base_df["Region"].astype(str).str.contains("아프리카|africa", case=False, regex=True, na=False)
    if africa_mask.any():
        base_df = base_df[africa_mask].copy()

year_values = sorted([int(x) for x in base_df["Year"].dropna().unique()])
country_values = sorted(base_df["Country"].dropna().unique().tolist())

selected_years = st.sidebar.multiselect(
    "Year",
    year_values,
    default=year_values,
)

selected_country = st.sidebar.selectbox(
    "Country",
    ["All Countries"] + country_values,
)

filtered = base_df.copy()
if selected_years:
    filtered = filtered[filtered["Year"].isin(selected_years)]
if selected_country != "All Countries":
    filtered = filtered[filtered["Country"] == selected_country]

company_values = sorted(filtered["Company"].dropna().unique().tolist())
selected_company = st.sidebar.selectbox(
    "Company",
    ["All Companies"] + company_values,
)

if selected_company != "All Companies":
    filtered = filtered[filtered["Company"] == selected_company]

st.sidebar.caption(f"Data source: {source_label}")
st.sidebar.caption(f"Loaded rows: {len(df):,}")

# KPI row
sales_total = filtered["Sales KRW"].sum()
qty_total = filtered["Quantity"].sum()
country_count = filtered["Country"].nunique()
company_count = filtered["Company"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Sales (KRW)", format_krw(sales_total))
k2.metric("Quantity", f"{qty_total:,.0f}")
k3.metric("Countries", f"{country_count:,}")
k4.metric("Companies", f"{company_count:,}")

st.markdown("---")

overview_tab, company_tab, product_tab, device_tab, quality_tab = st.tabs(
    ["Overview", "Company", "Product", "Device Base", "Data Quality"]
)

with overview_tab:
    left, right = st.columns([1.15, 0.85])

    with left:
        st.subheader("Sales by Country")
        country_sales = (
            filtered.groupby("Country", as_index=False)["Sales KRW"]
            .sum()
            .sort_values("Sales KRW", ascending=False)
        )
        if not country_sales.empty:
            fig = px.bar(
                country_sales.head(20),
                x="Sales KRW",
                y="Country",
                orientation="h",
                text_auto=".2s",
            )
            fig.update_layout(
                height=max(420, len(country_sales.head(20)) * 28),
                yaxis={"categoryorder": "total ascending"},
                xaxis_title="Sales (KRW)",
                yaxis_title="",
                margin=dict(l=10, r=10, t=20, b=10),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with right:
        st.subheader("Top Companies")
        company_sales = (
            filtered.groupby(["Country", "Company"], as_index=False)["Sales KRW"]
            .sum()
            .sort_values("Sales KRW", ascending=False)
            .head(15)
        )
        company_sales["Sales KRW"] = company_sales["Sales KRW"].round(0)
        st.dataframe(company_sales, use_container_width=True, hide_index=True)

    st.subheader("Yearly Sales Trend")
    yearly = filtered.groupby("Year", as_index=False)["Sales KRW"].sum().dropna()
    if not yearly.empty:
        yearly["Year"] = yearly["Year"].astype(int)
        fig = px.line(yearly, x="Year", y="Sales KRW", markers=True)
        fig.update_layout(
            height=360,
            xaxis_title="Year",
            yaxis_title="Sales (KRW)",
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with company_tab:
    st.subheader("Company Portfolio")
    if selected_country == "All Countries":
        st.info("Select a country in the sidebar to see the companies in that market.")
    else:
        company_table = (
            base_df[base_df["Country"] == selected_country]
            .groupby("Company", as_index=False)
            .agg(
                Sales_KRW=("Sales KRW", "sum"),
                Quantity=("Quantity", "sum"),
                Products=("Item", "nunique"),
                First_Sale=("Date", "min"),
                Last_Sale=("Date", "max"),
            )
            .sort_values("Sales_KRW", ascending=False)
        )
        st.dataframe(company_table, use_container_width=True, hide_index=True)

        st.subheader("Company Sales Trend")
        trend_source = base_df[base_df["Country"] == selected_country].copy()
        if selected_company != "All Companies":
            trend_source = trend_source[trend_source["Company"] == selected_company]

        trend = (
            trend_source.dropna(subset=["Date"])
            .assign(Period=lambda x: x["Date"].dt.to_period("M").dt.to_timestamp())
            .groupby(["Period", "Company"], as_index=False)["Sales KRW"]
            .sum()
        )
        if not trend.empty:
            if selected_company == "All Companies":
                top_names = company_table.head(8)["Company"].tolist()
                trend = trend[trend["Company"].isin(top_names)]
            fig = px.line(trend, x="Period", y="Sales KRW", color="Company")
            fig.update_layout(height=420, xaxis_title="", yaxis_title="Sales (KRW)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with product_tab:
    st.subheader("Product Mix")
    product_summary = (
        filtered.groupby(["Item Code", "Item"], as_index=False)
        .agg(Sales_KRW=("Sales KRW", "sum"), Quantity=("Quantity", "sum"))
        .sort_values("Sales_KRW", ascending=False)
    )
    st.dataframe(product_summary.head(50), use_container_width=True, hide_index=True)

    chart_data = product_summary.head(15)
    if not chart_data.empty:
        fig = px.bar(chart_data, x="Sales_KRW", y="Item", orientation="h")
        fig.update_layout(
            height=520,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Sales (KRW)",
            yaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with device_tab:
    st.subheader("Device Installed / Shipment Base")
    device_df = filtered[
        filtered["Level 1"].str.upper().eq("완제품")
        & filtered["Level 2"].str.contains("기기", na=False)
    ].copy()

    if device_df.empty:
        st.info("No device rows were found for the current filters.")
    else:
        device_df["Platform"] = device_df["Item"].apply(classify_device)
        device_summary = (
            device_df.groupby(["Country", "Company", "Platform"], as_index=False)["Quantity"]
            .sum()
            .sort_values("Quantity", ascending=False)
        )
        st.dataframe(device_summary, use_container_width=True, hide_index=True)

        platform = device_df.groupby("Platform", as_index=False)["Quantity"].sum()
        fig = px.bar(platform, x="Platform", y="Quantity", text_auto=".0f")
        fig.update_layout(height=380, xaxis_title="", yaxis_title="Units")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with quality_tab:
    st.subheader("Data Quality")
    q1, q2, q3 = st.columns(3)
    q1.metric("Rows", f"{len(df):,}")
    q2.metric("Missing Country", f"{(df['Country'] == '').sum():,}")
    q3.metric("Missing Date", f"{df['Date'].isna().sum():,}")

    st.markdown("#### Loaded files")
    file_summary = (
        df.groupby("Source File", as_index=False)
        .agg(
            Rows=("Source File", "size"),
            Countries=("Country", "nunique"),
            Companies=("Company", "nunique"),
            Min_Date=("Date", "min"),
            Max_Date=("Date", "max"),
        )
    )
    st.dataframe(file_summary, use_container_width=True, hide_index=True)

    st.markdown("#### Raw standardized data")
    st.dataframe(df.head(500), use_container_width=True, hide_index=True)

from pathlib import Path

import pandas as pd
import streamlit as st

# Configure the page before displaying anything.
st.set_page_config(
    page_title="Retail Intelligence",
    page_icon="📊",
    layout="wide",
)

st.title("Retail Intelligence Dashboard")
st.write(
    "Explore fictional retail sales, gross profit, and inventory waste."
)

# Find the CSV relative to this Python file.
data_file = Path(__file__).parent / "data" / "sales.csv"

if not data_file.exists():
    st.error("Sales data not found. Run: python generate_data.py")
    st.stop()

df = pd.read_csv(data_file, parse_dates=["date"])

# Calculate financial metrics from the underlying data.
df["revenue"] = df["units_sold"] * df["unit_price"]
df["cost_of_goods_sold"] = df["units_sold"] * df["unit_cost"]
df["gross_profit"] = df["revenue"] - df["cost_of_goods_sold"]
df["waste_cost"] = df["waste_units"] * df["unit_cost"]

# Sidebar filters.
st.sidebar.header("Filters")

regions = sorted(df["region"].unique())
selected_regions = st.sidebar.multiselect(
    "Choose regions",
    options=regions,
    default=regions,
)

categories = sorted(df["category"].unique())
selected_categories = st.sidebar.multiselect(
    "Choose categories",
    options=categories,
    default=categories,
)

start_date = st.sidebar.date_input(
    "Start date",
    value=df["date"].min().date(),
)

end_date = st.sidebar.date_input(
    "End date",
    value=df["date"].max().date(),
)

if start_date > end_date:
    st.error("The start date must be on or before the end date.")
    st.stop()

filtered = df[
    df["region"].isin(selected_regions)
    & df["category"].isin(selected_categories)
    & (df["date"].dt.date >= start_date)
    & (df["date"].dt.date <= end_date)
].copy()

if filtered.empty:
    st.warning("No records match these filters.")
    st.stop()

# Summary metrics.
revenue = filtered["revenue"].sum()
profit = filtered["gross_profit"].sum()
waste = filtered["waste_cost"].sum()
margin = profit / revenue if revenue else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Revenue", f"${revenue:,.2f}")
col2.metric("Gross profit", f"${profit:,.2f}")
col3.metric("Gross margin", f"{margin:.1%}")
col4.metric("Waste cost", f"${waste:,.2f}")

st.caption(
    "Currency is illustrative. Values are calculated from fictional data."
)

# Revenue by product category.
st.subheader("Revenue by category")

category_sales = (
    filtered.groupby("category")["revenue"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(category_sales)

# Revenue and profit over time.
st.subheader("Monthly performance")

monthly = (
    filtered.set_index("date")
    .resample("MS")[["revenue", "gross_profit"]]
    .sum()
)

st.line_chart(monthly)

# Region comparison.
st.subheader("Performance by region")

region_summary = (
    filtered.groupby("region")
    .agg(
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
        waste_cost=("waste_cost", "sum"),
        units_sold=("units_sold", "sum"),
    )
    .sort_values("revenue", ascending=False)
)

st.dataframe(region_summary.round(2), use_container_width=True)

# A basic, deterministic business finding.
top_category = category_sales.index[0]
top_region = region_summary["revenue"].idxmax()

st.subheader("Automated observations")
st.write(
    f"- **Top category by revenue:** {top_category}."
)
st.write(
    f"- **Top region by revenue:** {top_region}."
)
st.write(
    f"- **Estimated waste cost:** ${waste:,.2f}."
)

# Allow the user to download the filtered results.
csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data",
    data=csv_data,
    file_name="filtered_sales.csv",
    mime="text/csv",
)
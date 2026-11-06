from pathlib import Path

import pandas as pd
import streamlit as st
import json
import hashlib

from ai_report import generate_ai_report

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


# ==========================================
# AI MANAGEMENT REPORT
# ==========================================

st.divider()

st.subheader("AI-Powered Management Report")

st.write(
    "Generate an AI-assisted analysis of the "
    "business performance currently displayed "
    "in your dashboard."
)


# Calculate additional business metrics.
total_units_sold = int(filtered["units_sold"].sum())
total_waste_units = int(filtered["waste_units"].sum())

waste_percentage_revenue = (
    waste / revenue * 100 if revenue else 0
)

waste_percentage_cogs = (
    waste / filtered["cost_of_goods_sold"].sum() * 100
    if filtered["cost_of_goods_sold"].sum() else 0
)


# Prepare category performance.
category_performance = {
    str(category): round(float(value), 2)
    for category, value in category_sales.items()
}


# Prepare regional performance.
regional_performance = {}

for region, row in region_summary.iterrows():

    regional_performance[str(region)] = {
        "revenue": round(float(row["revenue"]), 2),
        "gross_profit": round(float(row["gross_profit"]), 2),
        "waste_cost": round(float(row["waste_cost"]), 2),
        "units_sold": int(row["units_sold"])
    }


# Prepare monthly performance.
monthly_performance = {}

for date, row in monthly.iterrows():

    monthly_performance[date.strftime("%Y-%m")] = {
        "revenue": round(float(row["revenue"]), 2),
        "gross_profit": round(float(row["gross_profit"]), 2)
    }


# Assemble the complete business metrics dictionary.
business_metrics = {

    "reporting_period": {
        "start_date": str(start_date),
        "end_date": str(end_date)
    },

    "selected_regions": selected_regions,
    "selected_categories": selected_categories,

    "financial_performance": {
        "total_revenue": round(float(revenue), 2),
        "cost_of_goods_sold": round(
            float(filtered["cost_of_goods_sold"].sum()), 2
        ),
        "gross_profit": round(float(profit), 2),
        "gross_margin_percentage": round(float(margin * 100), 2)
    },

    "inventory_performance": {
        "total_waste_cost": round(float(waste), 2),
        "total_waste_units": total_waste_units,
        "waste_percentage_of_revenue": round(
            waste_percentage_revenue, 2
        ),
        "waste_percentage_of_cogs": round(
            waste_percentage_cogs, 2
        ),
        "total_units_sold": total_units_sold
    },

    "top_performers": {
        "highest_revenue_category": str(top_category),
        "highest_revenue_region": str(top_region)
    },

    "category_performance": category_performance,

    "regional_performance": regional_performance,

    "monthly_performance": monthly_performance,

    "accounting_note": (
        "Gross profit is revenue minus COGS on units sold. "
        "Waste cost is calculated separately and is not "
        "subtracted from gross profit in this dashboard."
    )
}


# Create a fingerprint of the current dashboard selection.
# This helps us identify when filters have changed.
metrics_json = json.dumps(
    business_metrics,
    sort_keys=True
)

current_signature = hashlib.sha256(
    metrics_json.encode("utf-8")
).hexdigest()


# Generate report only when the button is clicked.
if st.button(
    "Generate AI Management Report",
    type="primary"
):

    try:

        with st.spinner(
            "Gemini is analysing your business performance. "
            "This may take a few minutes."
        ):

            report = generate_ai_report(business_metrics)

            st.session_state["ai_report"] = report

            st.session_state["ai_report_signature"] = (
                current_signature
            )

    except Exception as error:

        st.error(
            f"Unable to generate the AI report: {error}"
        )


# Display the report if it matches the current filters.
if "ai_report" in st.session_state:

    if (
        st.session_state.get("ai_report_signature")
        == current_signature
    ):

        st.divider()

        st.markdown(
            st.session_state["ai_report"]
        )

    else:

        st.info(
            "Your dashboard filters have changed. "
            "Generate a new report to analyse the updated data."
        )

# Allow the user to download the filtered results.
csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data",
    data=csv_data,
    file_name="filtered_sales.csv",
    mime="text/csv",
)
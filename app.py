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

# ==========================================
# MONTH-OVER-MONTH TREND ANALYSIS
# ==========================================

monthly["revenue_change"] = monthly["revenue"].pct_change() * 100

monthly["profit_change"] = monthly["gross_profit"].pct_change() * 100

monthly["revenue_declining"] = monthly["revenue_change"] < 0

monthly["profit_declining"] = monthly["profit_change"] < 0

revenue_decline_months = int(monthly["revenue_declining"].sum())

profit_decline_months = int(monthly["profit_declining"].sum())

revenue_decline_details = monthly.loc[
    monthly["revenue_declining"],
    ["revenue", "revenue_change"]
].round(2).to_dict("index")

profit_decline_details = monthly.loc[
    monthly["profit_declining"],
    ["gross_profit", "profit_change"]
].round(2).to_dict("index")

# ==========================================
# CONSECUTIVE DECLINE DETECTION
# ==========================================

def calculate_decline_streak(decline_series):
    current_streak = 0
    longest_streak = 0

    for declining in decline_series.fillna(False):
        if declining:
            current_streak += 1
            longest_streak = max(
                longest_streak,
                current_streak
            )
        else:
            current_streak = 0

    return {
        "current_consecutive_declines": current_streak,
        "longest_consecutive_declines": longest_streak
    }


revenue_decline_streak = calculate_decline_streak(
    monthly["revenue_declining"]
)

profit_decline_streak = calculate_decline_streak(
    monthly["profit_declining"]
)

# ==========================================
# PRODUCT AND CATEGORY PERFORMANCE
# ==========================================

# Calculate monthly revenue for each product.
product_monthly = (
    filtered.assign(
        revenue=filtered["units_sold"] * filtered["unit_price"]
    )
    .groupby([
        pd.Grouper(key="date", freq="MS"),
        "product",
        "category"
    ])["revenue"]
    .sum()
    .reset_index()
)

# Calculate monthly revenue changes for each product.
product_monthly["revenue_change"] = (
    product_monthly
    .groupby("product")["revenue"]
    .pct_change() * 100
)

# Identify products with declining revenue.
product_monthly["revenue_declining"] = (
    product_monthly["revenue_change"] < 0
)

# Calculate monthly revenue for each category.
category_monthly = (
    filtered.assign(
        revenue=filtered["units_sold"] * filtered["unit_price"]
    )
    .groupby([
        pd.Grouper(key="date", freq="MS"),
        "category"
    ])["revenue"]
    .sum()
    .reset_index()
)

# Calculate monthly revenue changes for each category.
category_monthly["revenue_change"] = (
    category_monthly
    .groupby("category")["revenue"]
    .pct_change() * 100
)

category_monthly["revenue_declining"] = (
    category_monthly["revenue_change"] < 0
)

# ==========================================
# BIGGEST REVENUE DECLINES
# ==========================================

# Compare each product's latest month with its previous month.
product_changes = product_monthly.dropna(
    subset=["revenue_change"]
).sort_values("revenue_change")

# Compare each category's latest month with its previous month.
category_changes = category_monthly.dropna(
    subset=["revenue_change"]
).sort_values("revenue_change")

# Get the five products with the largest percentage declines.
biggest_product_declines = (
    product_changes[
        product_changes["revenue_declining"]
    ]
    .groupby("product")
    .tail(1)
    .sort_values("revenue_change")
    .head(5)
)

# Get the five categories with the largest percentage declines.
biggest_category_declines = (
    category_changes[
        category_changes["revenue_declining"]
    ]
    .groupby("category")
    .tail(1)
    .sort_values("revenue_change")
    .head(5)
)

# ==========================================
# REVENUE LOSS CALCULATION
# ==========================================

biggest_product_declines = biggest_product_declines.copy()

biggest_product_declines["previous_revenue"] = (
    biggest_product_declines["revenue"]
    / (1 + biggest_product_declines["revenue_change"] / 100)
)

biggest_product_declines["revenue_lost"] = (
    biggest_product_declines["previous_revenue"]
    - biggest_product_declines["revenue"]
)

biggest_category_declines = biggest_category_declines.copy()

biggest_category_declines["previous_revenue"] = (
    biggest_category_declines["revenue"]
    / (1 + biggest_category_declines["revenue_change"] / 100)
)

biggest_category_declines["revenue_lost"] = (
    biggest_category_declines["previous_revenue"]
    - biggest_category_declines["revenue"]
)

# ==========================================
# REGIONAL TREND ANALYSIS
# ==========================================

regional_monthly = (
    filtered.assign(
        revenue=filtered["units_sold"] * filtered["unit_price"],
        gross_profit=(
            filtered["units_sold"]
            * (filtered["unit_price"] - filtered["unit_cost"])
        )
    )
    .groupby([
        pd.Grouper(key="date", freq="MS"),
        "region"
    ])[["revenue", "gross_profit"]]
    .sum()
    .reset_index()
)

# Calculate monthly changes for each region.
regional_monthly["revenue_change"] = (
    regional_monthly
    .groupby("region")["revenue"]
    .pct_change() * 100
)

regional_monthly["profit_change"] = (
    regional_monthly
    .groupby("region")["gross_profit"]
    .pct_change() * 100
)

# Identify declining regional performance.
regional_monthly["revenue_declining"] = (
    regional_monthly["revenue_change"] < 0
)

regional_monthly["profit_declining"] = (
    regional_monthly["profit_change"] < 0
)

# ==========================================
# BIGGEST REGIONAL DECLINES
# ==========================================

# Sort regional data chronologically.
regional_changes = regional_monthly.sort_values("date")

# Get each region's latest monthly performance.
regional_latest_changes = (
    regional_changes
    .groupby("region")
    .tail(1)
)

# Identify regions with declining revenue.
biggest_regional_revenue_declines = (
    regional_latest_changes
    .dropna(subset=["revenue_change"])
    .loc[lambda df: df["revenue_declining"]]
    .sort_values("revenue_change")
)

# Identify regions with declining gross profit.
biggest_regional_profit_declines = (
    regional_latest_changes
    .dropna(subset=["profit_change"])
    .loc[lambda df: df["profit_declining"]]
    .sort_values("profit_change")
)

# Calculate previous-month revenue and gross profit.
biggest_regional_revenue_declines = (
    biggest_regional_revenue_declines.copy()
)

biggest_regional_revenue_declines["previous_revenue"] = (
    biggest_regional_revenue_declines["revenue"]
    / (1 + biggest_regional_revenue_declines["revenue_change"] / 100)
)

biggest_regional_revenue_declines["revenue_lost"] = (
    biggest_regional_revenue_declines["previous_revenue"]
    - biggest_regional_revenue_declines["revenue"]
)

biggest_regional_profit_declines = (
    biggest_regional_profit_declines.copy()
)

biggest_regional_profit_declines["previous_gross_profit"] = (
    biggest_regional_profit_declines["gross_profit"]
    / (1 + biggest_regional_profit_declines["profit_change"] / 100)
)

biggest_regional_profit_declines["gross_profit_lost"] = (
    biggest_regional_profit_declines["previous_gross_profit"]
    - biggest_regional_profit_declines["gross_profit"]
)

# ==========================================
# BUSINESS METRICS ASSEMBLY
# ==========================================

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
    
    "monthly_trend_analysis": {
        "months_with_revenue_decline": revenue_decline_months,
        "months_with_gross_profit_decline": profit_decline_months,
        "revenue_decline_details": {
            str(date): details
            for date, details in revenue_decline_details.items()
        },
        "profit_decline_details": {
            str(date): details
            for date, details in profit_decline_details.items()
        },
        "consecutive_decline_analysis": {
            "revenue": revenue_decline_streak,
            "gross_profit": profit_decline_streak
        },
        "product_category_analysis": {
            "biggest_product_declines": biggest_product_declines[
                ["product", "category", "revenue", "revenue_change", "revenue_lost"]
            ].round(2).to_dict("records"),

            "biggest_category_declines": biggest_category_declines[
                ["category", "revenue", "revenue_change", "revenue_lost"]
            ].round(2).to_dict("records")
        },
        "regional_trend_analysis": {
            "biggest_regional_revenue_declines": (
                biggest_regional_revenue_declines[
                    ["region", "revenue", "revenue_change", "revenue_lost"]
                ].round(2).to_dict("records")
            ),
            "biggest_regional_profit_declines": (
                biggest_regional_profit_declines[
                    ["region", "gross_profit", "profit_change", "gross_profit_lost"]
                ].round(2).to_dict("records")
            )
        },
    },

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
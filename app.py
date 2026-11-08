from pathlib import Path

import hashlib
import json

import pandas as pd
import streamlit as st

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

df["total_units_handled"] = df["units_sold"] + df["waste_units"]

total_units_handled = df["total_units_handled"].sum()
total_waste_units = df["waste_units"].sum()

waste_rate = (
    (total_waste_units / total_units_handled) * 100
    if total_units_handled > 0
    else 0
)

waste_by_product = (
    df.groupby("product")
    .agg(
        waste_units=("waste_units", "sum"),
        waste_cost=("waste_cost", "sum")
    )
    .reset_index()
    .sort_values("waste_cost", ascending=False)
)

waste_by_category = (
    df.groupby("category")
    .agg(
        waste_units=("waste_units", "sum"),
        waste_cost=("waste_cost", "sum")
    )
    .reset_index()
    .sort_values("waste_cost", ascending=False)
)

waste_by_region = (
    df.groupby("region")
    .agg(
        waste_units=("waste_units", "sum"),
        waste_cost=("waste_cost", "sum")
    )
    .reset_index()
    .sort_values("waste_cost", ascending=False)
)

waste_by_month = (
    df.groupby(df["date"].dt.to_period("M"))
    .agg(
        waste_units=("waste_units", "sum"),
        waste_cost=("waste_cost", "sum")
    )
    .reset_index()
)

waste_by_month["date"] = waste_by_month["date"].astype(str)
waste_by_month = waste_by_month.sort_values("date")

total_waste_cost = df["waste_cost"].sum()
total_revenue = df["revenue"].sum()

waste_to_revenue_ratio = (
    (total_waste_cost / total_revenue) * 100
    if total_revenue > 0
    else 0
)


# Sidebar filters.
st.sidebar.header("Filters")

regions = sorted(df["region"].dropna().unique())
selected_regions = st.sidebar.multiselect(
    "Choose regions",
    options=regions,
    default=regions,
)

categories = sorted(df["category"].dropna().unique())
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
st.write(f"- **Top category by revenue:** {top_category}.")
st.write(f"- **Top region by revenue:** {top_region}.")
st.write(f"- **Estimated waste cost:** ${waste:,.2f}.")


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


# ==========================================
# ADDITIONAL BUSINESS METRICS
# ==========================================

total_units_sold = int(filtered["units_sold"].sum())
total_waste_units = int(filtered["waste_units"].sum())

total_cogs = filtered["cost_of_goods_sold"].sum()

waste_percentage_revenue = (
    waste / revenue * 100 if revenue else 0
)

waste_percentage_cogs = (
    waste / total_cogs * 100 if total_cogs else 0
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
        "units_sold": int(row["units_sold"]),
    }


# ==========================================
# COMPLETE-MONTH COMPARISON PERIOD
# ==========================================

# Month-over-month comparisons use complete calendar months only.
# Partial first or last months are excluded to avoid comparing
# different numbers of days.

start_timestamp = pd.Timestamp(start_date)
end_timestamp = pd.Timestamp(end_date)

first_complete_month = start_timestamp.to_period("M").to_timestamp()
if start_timestamp.day != 1:
    first_complete_month += pd.offsets.MonthBegin(1)

last_complete_month = end_timestamp.to_period("M").to_timestamp()
if end_timestamp != last_complete_month + pd.offsets.MonthEnd(0):
    last_complete_month -= pd.offsets.MonthBegin(1)

if first_complete_month <= last_complete_month:
    complete_months = pd.date_range(
        first_complete_month,
        last_complete_month,
        freq="MS",
    )
else:
    complete_months = pd.DatetimeIndex([])

monthly_analysis = monthly.reindex(complete_months)


def calculate_percentage_change(current, previous):
    """Calculate percentage change only when the previous value is positive."""
    valid_previous = previous.where(previous > 0)
    return (current - previous) / valid_previous * 100


# ==========================================
# MONTH-OVER-MONTH TREND ANALYSIS
# ==========================================

monthly_analysis["revenue_change"] = calculate_percentage_change(
    monthly_analysis["revenue"],
    monthly_analysis["revenue"].shift(1),
)

monthly_analysis["profit_change"] = calculate_percentage_change(
    monthly_analysis["gross_profit"],
    monthly_analysis["gross_profit"].shift(1),
)

monthly_analysis["revenue_declining"] = (
    monthly_analysis["revenue"]
    < monthly_analysis["revenue"].shift(1)
) & monthly_analysis["revenue"].shift(1).gt(0)

monthly_analysis["profit_declining"] = (
    monthly_analysis["gross_profit"]
    < monthly_analysis["gross_profit"].shift(1)
) & monthly_analysis["gross_profit"].shift(1).gt(0)

revenue_decline_months = int(
    monthly_analysis["revenue_declining"].sum()
)

profit_decline_months = int(
    monthly_analysis["profit_declining"].sum()
)

revenue_decline_details = (
    monthly_analysis.loc[
        monthly_analysis["revenue_declining"],
        ["revenue", "revenue_change"],
    ]
    .round(2)
    .to_dict("index")
)

profit_decline_details = (
    monthly_analysis.loc[
        monthly_analysis["profit_declining"],
        ["gross_profit", "profit_change"],
    ]
    .round(2)
    .to_dict("index")
)

monthly_performance = {
    date.strftime("%Y-%m"): {
        "revenue": round(float(row["revenue"]), 2),
        "gross_profit": round(float(row["gross_profit"]), 2),
    }
    for date, row in monthly_analysis[["revenue", "gross_profit"]].iterrows()
}


# ==========================================
# DAILY ANOMALY DETECTION
# ==========================================

# Use the filtered data so anomaly results match the dashboard selections.
daily = (
    filtered.groupby("date")[["revenue", "gross_profit", "waste_cost"]]
    .sum()
    .reset_index()
)

MINIMUM_DAILY_OBSERVATIONS = 30


def detect_anomalies(data, column):
    """
    Detect IQR outliers when at least 30 daily observations are available.
    Returns anomaly rows, lower/upper bounds, and analysis status.
    """
    observations = data[column].dropna()

    if len(observations) < MINIMUM_DAILY_OBSERVATIONS:
        return data.iloc[0:0].copy(), None, None, "insufficient_data"

    q1 = observations.quantile(0.25)
    q3 = observations.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    anomalies = data[
        (data[column] < lower_bound)
        | (data[column] > upper_bound)
    ].copy()

    anomalies["anomaly_type"] = anomalies[column].apply(
        lambda value: (
            "Unusually high" if value > upper_bound
            else "Unusually low"
        )
    )

    return anomalies, lower_bound, upper_bound, "analysed"


(
    revenue_anomalies,
    revenue_lower,
    revenue_upper,
    revenue_anomaly_status,
) = detect_anomalies(daily, "revenue")

(
    profit_anomalies,
    profit_lower,
    profit_upper,
    profit_anomaly_status,
) = detect_anomalies(daily, "gross_profit")

(
    waste_anomalies,
    waste_lower,
    waste_upper,
    waste_anomaly_status,
) = detect_anomalies(daily, "waste_cost")


anomaly_summary = {
    "Revenue": len(revenue_anomalies),
    "Gross Profit": len(profit_anomalies),
    "Waste Cost": len(waste_anomalies),
}

anomaly_status = {
    "Revenue": revenue_anomaly_status,
    "Gross Profit": profit_anomaly_status,
    "Waste Cost": waste_anomaly_status,
}


def rounded_or_none(value):
    if value is None or pd.isna(value):
        return None
    return round(float(value), 2)


def anomaly_records(data, column):
    if data.empty:
        return []

    records = data[["date", column, "anomaly_type"]].copy()
    records["date"] = records["date"].dt.strftime("%Y-%m-%d")
    records[column] = records[column].round(2)

    return records.to_dict("records")


# ==========================================
# CONSECUTIVE DECLINE DETECTION
# ==========================================

def calculate_decline_streak(decline_series):
    current_streak = 0
    longest_streak = 0

    for declining in decline_series.fillna(False):
        if declining:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0

    return {
        "current_consecutive_declines": current_streak,
        "longest_consecutive_declines": longest_streak,
    }


if len(complete_months) >= 2:
    revenue_decline_streak = calculate_decline_streak(
        monthly_analysis["revenue_declining"]
    )

    profit_decline_streak = calculate_decline_streak(
        monthly_analysis["profit_declining"]
    )

    monthly_trend_status = "analysed"
else:
    revenue_decline_streak = {
        "current_consecutive_declines": None,
        "longest_consecutive_declines": None,
    }

    profit_decline_streak = {
        "current_consecutive_declines": None,
        "longest_consecutive_declines": None,
    }

    monthly_trend_status = "insufficient_complete_months"


# ==========================================
# PRODUCT AND CATEGORY PERFORMANCE
# ==========================================

def build_entity_monthly_performance(data, entity_columns, months):
    """
    Create a complete month-by-month series for each entity.
    Missing entity-month combinations are treated as zero revenue.
    """
    output_columns = (
        entity_columns
        + [
            "date",
            "revenue",
            "previous_revenue",
            "revenue_change",
            "revenue_lost",
            "revenue_declining",
        ]
    )

    if len(months) < 2:
        return pd.DataFrame(columns=output_columns)

    entities = data[entity_columns].drop_duplicates().copy()
    month_frame = pd.DataFrame({"date": months})

    entities["_key"] = 1
    month_frame["_key"] = 1

    grid = (
        entities.merge(month_frame, on="_key")
        .drop(columns="_key")
    )

    actual_monthly = (
        data.groupby(
            entity_columns + [pd.Grouper(key="date", freq="MS")]
        )["revenue"]
        .sum()
        .reset_index()
    )

    grid = grid.merge(
        actual_monthly,
        on=entity_columns + ["date"],
        how="left",
    )

    grid["revenue"] = grid["revenue"].fillna(0.0)
    grid = grid.sort_values(entity_columns + ["date"]).reset_index(drop=True)

    grid["previous_revenue"] = (
        grid.groupby(entity_columns, sort=False)["revenue"].shift(1)
    )

    grid["revenue_change"] = calculate_percentage_change(
        grid["revenue"],
        grid["previous_revenue"],
    )

    grid["revenue_declining"] = (
        grid["previous_revenue"].gt(0)
        & grid["revenue"].lt(grid["previous_revenue"])
    )

    grid["revenue_lost"] = (
        grid["previous_revenue"] - grid["revenue"]
    ).where(grid["revenue_declining"])

    return grid


product_monthly = build_entity_monthly_performance(
    filtered,
    ["product", "category"],
    complete_months,
)

category_monthly = build_entity_monthly_performance(
    filtered,
    ["category"],
    complete_months,
)


def get_latest_entity_declines(monthly_data, limit=5):
    if monthly_data.empty:
        return monthly_data.copy()

    latest_month = monthly_data["date"].max()

    latest = monthly_data[
        monthly_data["date"] == latest_month
    ].copy()

    declines = latest[latest["revenue_declining"]].copy()

    return (
        declines.sort_values(
            ["revenue_lost", "revenue_change"],
            ascending=[False, True],
        )
        .head(limit)
        .reset_index(drop=True)
    )


biggest_product_declines = get_latest_entity_declines(product_monthly)
biggest_category_declines = get_latest_entity_declines(category_monthly)


# ==========================================
# REGIONAL TREND ANALYSIS
# ==========================================

def build_regional_monthly_performance(data, months):
    columns = [
        "region",
        "date",
        "revenue",
        "gross_profit",
        "previous_revenue",
        "revenue_change",
        "revenue_lost",
        "revenue_declining",
        "previous_gross_profit",
        "profit_change",
        "gross_profit_lost",
        "profit_declining",
    ]

    if len(months) < 2:
        return pd.DataFrame(columns=columns)

    regions_frame = data[["region"]].drop_duplicates().copy()
    month_frame = pd.DataFrame({"date": months})

    regions_frame["_key"] = 1
    month_frame["_key"] = 1

    grid = (
        regions_frame.merge(month_frame, on="_key")
        .drop(columns="_key")
    )

    actual_monthly = (
        data.groupby(
            [pd.Grouper(key="date", freq="MS"), "region"]
        )[["revenue", "gross_profit"]]
        .sum()
        .reset_index()
    )

    grid = grid.merge(
        actual_monthly,
        on=["region", "date"],
        how="left",
    )

    grid[["revenue", "gross_profit"]] = (
        grid[["revenue", "gross_profit"]].fillna(0.0)
    )

    grid = grid.sort_values(["region", "date"]).reset_index(drop=True)

    grid["previous_revenue"] = (
        grid.groupby("region", sort=False)["revenue"].shift(1)
    )

    grid["revenue_change"] = calculate_percentage_change(
        grid["revenue"],
        grid["previous_revenue"],
    )

    grid["revenue_declining"] = (
        grid["previous_revenue"].gt(0)
        & grid["revenue"].lt(grid["previous_revenue"])
    )

    grid["revenue_lost"] = (
        grid["previous_revenue"] - grid["revenue"]
    ).where(grid["revenue_declining"])

    grid["previous_gross_profit"] = (
        grid.groupby("region", sort=False)["gross_profit"].shift(1)
    )

    grid["profit_change"] = calculate_percentage_change(
        grid["gross_profit"],
        grid["previous_gross_profit"],
    )

    grid["profit_declining"] = (
        grid["previous_gross_profit"].gt(0)
        & grid["gross_profit"].lt(grid["previous_gross_profit"])
    )

    grid["gross_profit_lost"] = (
        grid["previous_gross_profit"] - grid["gross_profit"]
    ).where(grid["profit_declining"])

    return grid


regional_monthly = build_regional_monthly_performance(
    filtered,
    complete_months,
)

if regional_monthly.empty:
    biggest_regional_revenue_declines = pd.DataFrame(
        columns=[
            "region", "revenue", "revenue_change", "revenue_lost"
        ]
    )

    biggest_regional_profit_declines = pd.DataFrame(
        columns=[
            "region", "gross_profit", "profit_change", "gross_profit_lost"
        ]
    )
else:
    latest_month = regional_monthly["date"].max()

    regional_latest_changes = regional_monthly[
        regional_monthly["date"] == latest_month
    ].copy()

    biggest_regional_revenue_declines = (
        regional_latest_changes[
            regional_latest_changes["revenue_declining"]
        ]
        .sort_values("revenue_lost", ascending=False)
        .reset_index(drop=True)
    )

    biggest_regional_profit_declines = (
        regional_latest_changes[
            regional_latest_changes["profit_declining"]
        ]
        .sort_values("gross_profit_lost", ascending=False)
        .reset_index(drop=True)
    )


# ==========================================
# BUSINESS METRICS ASSEMBLY
# ==========================================

business_metrics = {
    "reporting_period": {
        "start_date": str(start_date),
        "end_date": str(end_date),
    },

    "selected_regions": selected_regions,
    "selected_categories": selected_categories,

    "financial_performance": {
        "total_revenue": round(float(revenue), 2),
        "cost_of_goods_sold": round(float(total_cogs), 2),
        "gross_profit": round(float(profit), 2),
        "gross_margin_percentage": round(float(margin * 100), 2),
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
        "total_units_sold": total_units_sold,
    },

    "top_performers": {
        "highest_revenue_category": str(top_category),
        "highest_revenue_region": str(top_region),
    },

    "category_performance": category_performance,
    "regional_performance": regional_performance,
    "monthly_performance": monthly_performance,

    "monthly_trend_analysis": {
        "status": monthly_trend_status,
        "complete_months_included": [
            date.strftime("%Y-%m") for date in complete_months
        ],
        "months_with_revenue_decline": revenue_decline_months,
        "months_with_gross_profit_decline": profit_decline_months,
        "revenue_decline_details": {
            date.strftime("%Y-%m"): details
            for date, details in revenue_decline_details.items()
        },
        "profit_decline_details": {
            date.strftime("%Y-%m"): details
            for date, details in profit_decline_details.items()
        },
        "comparison_note": (
            "Month-over-month comparisons use complete calendar months "
            "only. Partial boundary months are excluded."
        ),
    },

    "consecutive_decline_analysis": {
        "status": monthly_trend_status,
        "revenue": revenue_decline_streak,
        "gross_profit": profit_decline_streak,
    },

    "product_category_analysis": {
        "status": (
            "analysed" if len(complete_months) >= 2
            else "insufficient_complete_months"
        ),
        "comparison_month": (
            complete_months[-1].strftime("%Y-%m")
            if len(complete_months) >= 2 else None
        ),
        "comparison_note": (
            "Each entity is compared with the immediately preceding "
            "calendar month. Missing entity-month sales are treated as "
            "zero. Percentage change is not calculated when the previous "
            "month's revenue is zero. Declines are ranked by actual "
            "revenue lost."
        ),
        "biggest_product_declines": (
            biggest_product_declines[
                [
                    "product",
                    "category",
                    "revenue",
                    "revenue_change",
                    "revenue_lost",
                ]
            ].round(2).to_dict("records")
        ),
        "biggest_category_declines": (
            biggest_category_declines[
                [
                    "category",
                    "revenue",
                    "revenue_change",
                    "revenue_lost",
                ]
            ].round(2).to_dict("records")
        ),
    },

    "regional_trend_analysis": {
        "status": (
            "analysed" if len(complete_months) >= 2
            else "insufficient_complete_months"
        ),
        "comparison_month": (
            complete_months[-1].strftime("%Y-%m")
            if len(complete_months) >= 2 else None
        ),
        "comparison_note": (
            "Each region is compared with the immediately preceding "
            "calendar month. Missing region-month sales are treated as "
            "zero. Percentage change is not calculated when the previous "
            "month's value is zero. Declines are ranked by actual "
            "monetary loss."
        ),
        "biggest_regional_revenue_declines": (
            biggest_regional_revenue_declines[
                ["region", "revenue", "revenue_change", "revenue_lost"]
            ].round(2).to_dict("records")
        ),
        "biggest_regional_profit_declines": (
            biggest_regional_profit_declines[
                [
                    "region",
                    "gross_profit",
                    "profit_change",
                    "gross_profit_lost",
                ]
            ].round(2).to_dict("records")
        ),
    },

    "anomaly_detection": {
        "method": "IQR applied to daily totals in the filtered dataset",
        "observation_definition": (
            "A daily observation is a date with at least one transaction "
            "matching the selected filters. Dates with no matching records "
            "are excluded rather than assumed to have zero sales."
        ),
        "minimum_daily_observations_required": MINIMUM_DAILY_OBSERVATIONS,
        "daily_observations": int(len(daily)),
        "summary": anomaly_summary,
        "status": anomaly_status,

        "revenue_thresholds": {
            "lower": rounded_or_none(revenue_lower),
            "upper": rounded_or_none(revenue_upper),
        },
        "profit_thresholds": {
            "lower": rounded_or_none(profit_lower),
            "upper": rounded_or_none(profit_upper),
        },
        "waste_thresholds": {
            "lower": rounded_or_none(waste_lower),
            "upper": rounded_or_none(waste_upper),
        },

        "revenue_anomalies": anomaly_records(
            revenue_anomalies, "revenue"
        ),
        "profit_anomalies": anomaly_records(
            profit_anomalies, "gross_profit"
        ),
        "waste_anomalies": anomaly_records(
            waste_anomalies, "waste_cost"
        ),
    },
    
    "inventory_waste": {
        "total_waste_units": int(total_waste_units),
        "total_units_handled": int(total_units_handled),
        "waste_rate_percent": round(waste_rate, 2),
        "total_waste_cost": round(total_waste_cost, 2),
        "waste_to_revenue_percent": round(waste_to_revenue_ratio, 2),
        "waste_by_product": waste_by_product.to_dict(orient="records"),
        "waste_by_category": waste_by_category.to_dict(orient="records"),
        "waste_by_region": waste_by_region.to_dict(orient="records"),
        "monthly_waste_trend": waste_by_month.to_dict(orient="records")
    },

    "accounting_note": (
        "Gross profit is revenue minus COGS on units sold. "
        "Waste cost is calculated separately and is not subtracted "
        "from gross profit in this dashboard. Currency is illustrative "
        "and is not specified by the dataset."
    ),
}


# Create a fingerprint of the current dashboard selection.
# This helps us identify when filters have changed.
metrics_json = json.dumps(
    business_metrics,
    sort_keys=True,
)

current_signature = hashlib.sha256(
    metrics_json.encode("utf-8")
).hexdigest()


# Generate report only when the button is clicked.
if st.button(
    "Generate AI Management Report",
    type="primary",
):
    try:
        with st.spinner(
            "Gemini is analysing your business performance. "
            "This may take a few minutes."
        ):
            report = generate_ai_report(business_metrics)

            st.session_state["ai_report"] = report
            st.session_state["ai_report_signature"] = current_signature

    except Exception as error:
        st.error(f"Unable to generate the AI report: {error}")


# Display the report if it matches the current filters.
if "ai_report" in st.session_state:
    if (
        st.session_state.get("ai_report_signature")
        == current_signature
    ):
        st.divider()
        st.markdown(st.session_state["ai_report"])
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

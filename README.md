
# Retail Intelligence Dashboard

## Overview
An interactive retail analytics application built with Python,
pandas, and Streamlit.

## Features
- Revenue, gross profit, gross margin, and waste-cost calculations
- Filtering by date, region, and product category
- Monthly performance charts
- Regional performance comparison
- Downloadable filtered data

## Technology
- Python
- pandas
- Streamlit
- Matplotlib
- CSV data

## Data
This project uses 500 fictional retail sales records generated
by `generate_data.py`. The data does not represent a real company.

## How to run

1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Generate the sample dataset with `python generate_data.py`.
4. Launch the application with `python -m streamlit run app.py`.

## Limitations
Gross profit excludes operating expenses. All financial values
are illustrative and are not forecasts or actual company results.
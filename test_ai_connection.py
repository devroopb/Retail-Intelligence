
from ai_report import generate_ai_report

test_metrics = {
    "total_revenue": 250000,
    "cost_of_goods_sold": 150000,
    "gross_profit": 100000,
    "gross_margin_percentage": 40,
    "inventory_waste_cost": 8000
}

print("Connecting to Google Gemini...")

try:
    report = generate_ai_report(test_metrics)

    print("\n========== AI MANAGEMENT REPORT ==========\n")
    print(report)
    print("\n========== END OF REPORT ==========")

except Exception as error:
    print("\nAPI request failed.")
    print("Error:", error)
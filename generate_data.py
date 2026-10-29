#pandas and numpy makes the table and the numerical values

from pathlib import Path

import numpy as np
import pandas as pd

# Make the random data reproducible.
rng = np.random.default_rng(42)

# Create 500 fictional sales records.
number_of_rows = 500

dates = pd.date_range(
    start="2025-01-01",
    end="2025-12-31",
    periods=number_of_rows,
)

#fictional prices, costs, categories where each row represents a single sales record
products = {
    "Apples": {"category": "Produce", "price": 3.50, "cost": 2.00},
    "Bananas": {"category": "Produce", "price": 2.20, "cost": 1.20},
    "Milk": {"category": "Dairy", "price": 5.00, "cost": 3.30},
    "Cheese": {"category": "Dairy", "price": 8.00, "cost": 5.40},
    "Bread": {"category": "Bakery", "price": 4.00, "cost": 2.10},
    "Muffins": {"category": "Bakery", "price": 6.00, "cost": 3.00},
    "Rice": {"category": "Pantry", "price": 12.00, "cost": 8.00},
    "Pasta": {"category": "Pantry", "price": 3.00, "cost": 1.50},
}

regions = ["Victoria", "Vancouver", "Surrey", "Nanaimo"]

rows = []

for i in range(number_of_rows):
    product = str(rng.choice(list(products.keys())))
    details = products[product]

    units = int(rng.integers(1, 21))
    price = details["price"]
    cost = details["cost"]

    # Fictional units discarded due to spoilage or damage.
    waste_units = int(rng.integers(0, 4))

    rows.append(
        {
            "date": dates[i].date().isoformat(),
            "region": str(rng.choice(regions)),
            "product": product,
            "category": details["category"],
            "units_sold": units,
            "unit_price": price,
            "unit_cost": cost,
            "waste_units": waste_units,
        }
    )

df = pd.DataFrame(rows)

# Save the data inside the project's data folder.
output_folder = Path(__file__).parent / "data"
output_folder.mkdir(exist_ok=True)

output_file = output_folder / "sales.csv"
#save as csv so both python and Excel can read it
df.to_csv(output_file, index=False)

print(f"Created {len(df)} fictional sales records.")
print(f"Saved to: {output_file}")
print(df.head())
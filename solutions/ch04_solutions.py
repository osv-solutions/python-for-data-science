"""Solutions to the Chapter 4 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch04_solutions.py

The explanations are in ch04_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(4)
n = 50 * 365 * 24
meters = pd.DataFrame({
    "meter": rng.integers(1, 51, size=n),
    "hour": rng.integers(0, 24, size=n),
    "kwh": rng.gamma(2.0, 0.6, size=n).round(3),
})
meters.to_csv("meters.csv", index=False)

# %% Exercise 4.1
tx = pd.read_csv("data/transactions.csv", parse_dates=["date"])
month = tx["date"].dt.month
cols = ["date", "description", "amount"]
print(tx.groupby(month).head(1)[cols].to_string(index=False))
print(tx.groupby(month).tail(1)[cols].to_string(index=False))

# %% Exercise 4.2
big = tx[tx["amount"].abs() > 100]
big.to_csv("big.csv", index=False)
back = pd.read_csv("big.csv", parse_dates=["date"])
print(len(big), len(back))
print(round(big["amount"].sum(), 2), round(back["amount"].sum(), 2))
print(back.equals(big.reset_index(drop=True)))

# %% Exercise 4.3
text = ("Sensor export\nGenerated 2026-07-01\n"
        "station\ttemp_c\thumidity\n"
        "north\t21.5\t40\nsouth\t-\t38\neast\t23.1\t-\n")
with open("sensors.tsv", "w", encoding="utf-8") as f:
    f.write(text)
sensors = pd.read_csv("sensors.tsv", sep="\t", skiprows=2,
                      na_values=["-"])
print(sensors)
print(sensors.dtypes)

# %% Exercise 4.4
orders = pd.read_excel("data/store_sales.xlsx", sheet_name="Orders",
                       header=2)
units = orders.groupby(["category", "product"])["units"].sum()
for category, product in units.groupby("category").idxmax():
    print(f"{category:<12}{product}")
with pd.ExcelWriter("by_category.xlsx") as writer:
    for category, part in orders.groupby("category"):
        part.to_excel(writer, sheet_name=category, index=False)
print(list(pd.read_excel("by_category.xlsx", sheet_name=None)))

# %% Exercise 4.5
import json

with open("data/orders.json", encoding="utf-8") as f:
    raw = json.load(f)
items = pd.json_normalize(raw, record_path="items",
                          meta=["order_id", ["customer", "name"]])
items["line_total"] = items["qty"] * items["price"]
per_order = items.groupby(["order_id", "customer.name"]).agg(
    items=("sku", "size"), total=("line_total", "sum"))
print(per_order.reset_index())

# %% Exercise 4.6
orders.to_csv("orders.csv", index=False)
orders.to_parquet("orders.parquet", index=False)
for name in ["orders.csv", "orders.parquet"]:
    print(f"{name:<16}{Path(name).stat().st_size:>7,} bytes")
two = pd.read_parquet("orders.parquet", columns=["region", "units"])
print(two.shape, two.dtypes.astype(str).tolist())

# %% Exercise 4.7
total = pd.Series(dtype=float)
largest = pd.Series(dtype=float)
for chunk in pd.read_csv("meters.csv", chunksize=100_000):
    by_meter = chunk.groupby("meter")["kwh"]
    total = total.add(by_meter.sum(), fill_value=0)
    largest = largest.combine(by_meter.max(), max, fill_value=0)
full = pd.read_csv("meters.csv").groupby("meter")["kwh"]
print((total.round(3) == full.sum().round(3)).all(),
      (largest == full.max()).all())
print(total.round(1).nlargest(3))

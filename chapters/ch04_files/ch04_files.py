"""Chapter 4: Loading Data from Files

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch04_files.py

or open the notebook and run the cells in order.
"""

# %% 4.1 CSV files
import pandas as pd

tx = pd.read_csv("data/transactions.csv")
print(tx.head(4))
print(tx.dtypes)

# %% 4.1 CSV files
tx = pd.read_csv("data/transactions.csv", parse_dates=["date"],
                 dtype={"category": "category"})
print(tx.dtypes)
print(tx["date"].min().date(), "to", tx["date"].max().date())
print(tx["date"].dt.month_name().value_counts().head(3))

# %% 4.1 CSV files
small = pd.read_csv("data/transactions.csv",
                    usecols=["date", "amount"], nrows=5)
print(small)
print(f"{len(tx)} rows, {tx['amount'].sum():,.2f} net")

# %% 4.1 CSV files
food = tx[tx["category"].isin(["Groceries", "Dining"])]
food.to_csv("food.csv", index=False)
for line in open("food.csv").read().splitlines()[:3]:
    print(line)

# %% 4.2 Messy CSV files
text = """Export from Konto 4711, created 2026-07-01
Datum;Beschreibung;Betrag
02.06.2026;Miete;-1.450,00
03.06.2026;Supermarkt;-62,35
05.06.2026;Gehalt;2.450,00
09.06.2026;Apotheke;n/a
"""
with open("konto.csv", "w", encoding="utf-8") as f:
    f.write(text)

# %% 4.2 Messy CSV files
print(pd.read_csv("konto.csv").head(3))

# %% 4.2 Messy CSV files
konto = pd.read_csv("konto.csv", sep=";", skiprows=1, decimal=",",
                    thousands=".", na_values=["n/a"],
                    dtype={"Datum": "str"})
konto["Datum"] = pd.to_datetime(konto["Datum"], format="%d.%m.%Y")
print(konto)
print(konto.dtypes)

# %% 4.2 Messy CSV files
cafe = "item,price\nCafé crème,3.80\nCrêpe,5.20\nMüsli,4.50\n"
with open("cafe.csv", "w", encoding="cp1252") as f:
    f.write(cafe)
try:
    pd.read_csv("cafe.csv")
except UnicodeDecodeError as err:
    print("UnicodeDecodeError:", str(err)[:52])
print(pd.read_csv("cafe.csv", encoding="cp1252"))

# %% 4.3 Excel workbooks
raw = pd.read_excel("data/store_sales.xlsx", sheet_name="Orders",
                    header=None, nrows=4)
print(raw.iloc[:, :3].to_string(max_colwidth=32))

# %% 4.3 Excel workbooks
orders = pd.read_excel("data/store_sales.xlsx", sheet_name="Orders",
                       header=2)
print(orders.shape)
print(orders.head(3))
print(orders.dtypes["order_date"])

# %% 4.3 Excel workbooks
book = pd.read_excel("data/store_sales.xlsx", sheet_name=None)
print(list(book))
print(book["Targets"])

# %% 4.4 JSON
import json

with open("data/orders.json", encoding="utf-8") as f:
    raw_orders = json.load(f)
from pprint import pprint

pprint(raw_orders[0], width=68)

# %% 4.4 JSON
flat = pd.json_normalize(raw_orders)
print(flat.columns.tolist())
print(flat[["order_id", "customer.city"]])

# %% 4.4 JSON
items = pd.json_normalize(raw_orders, record_path="items",
                          meta=["order_id", ["customer", "city"]])
items["line_total"] = items["qty"] * items["price"]
print(items)

# %% 4.5 Parquet
from pathlib import Path

tx.to_parquet("transactions.parquet", index=False)
back = pd.read_parquet("transactions.parquet")
print(back.dtypes)
for name in ["data/transactions.csv", "transactions.parquet"]:
    print(f"{name:<24}{Path(name).stat().st_size:>7,} bytes")

# %% 4.6 Big files in chunks
import numpy as np

rng = np.random.default_rng(4)
n = 50 * 365 * 24
meters = pd.DataFrame({
    "meter": rng.integers(1, 51, size=n),
    "hour": rng.integers(0, 24, size=n),
    "kwh": rng.gamma(2.0, 0.6, size=n).round(3),
})
meters.to_csv("meters.csv", index=False)
print(f"{n:,} rows, {Path('meters.csv').stat().st_size:,} bytes")

# %% 4.6 Big files in chunks
totals = pd.Series(dtype=float)
for chunk in pd.read_csv("meters.csv", chunksize=100_000):
    part = chunk.groupby("hour")["kwh"].sum()
    totals = totals.add(part, fill_value=0)
print(f"{totals.sum():,.0f} kWh in total")
print(totals.round(0).sort_values().tail(3))

# %% 4.7 Putting it together: the first-quarter targets report
orders = pd.read_excel("data/store_sales.xlsx", sheet_name="Orders",
                       header=2)
targets = pd.read_excel("data/store_sales.xlsx", sheet_name="Targets")
orders["revenue"] = orders["units"] * orders["unit_price"]
actual = orders.groupby("region")["revenue"].sum()
goal = targets.set_index("region")["q1_target"]
print(actual.round(0))

# %% 4.7 Putting it together: the first-quarter targets report
report = pd.DataFrame({"actual": actual.round(2), "target": goal})
report["gap"] = (report["actual"] - report["target"]).round(2)
report["pct"] = (report["actual"] / report["target"] * 100).round(1)
report = report.sort_values("pct")
print(report)
with pd.ExcelWriter("q1_report.xlsx") as writer:
    report.to_excel(writer, sheet_name="Summary")
    orders.to_excel(writer, sheet_name="Orders", index=False)

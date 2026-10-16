"""Solutions to the Chapter 13 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch13_solutions.py

The explanations are in ch13_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import sqlite3
from pathlib import Path

import pandas as pd

orders = pd.read_parquet("data/shop_orders.parquet")
customers = pd.read_csv("data/shop_customers.csv",
                        parse_dates=["joined"])
tickets = pd.read_csv("data/support_tickets.csv")
pattern = r"(?i)#?\bhc[-\s]?(\d{5})"
tickets["order_id"] = "HC-" + tickets["subject"].str.extract(pattern)[0]
for month, part in orders.groupby(orders["order_date"]
                                  .dt.to_period("M")):
    part.to_csv(f"orders_{month}.csv", index=False)

# %% Exercise 13.1
both = customers.merge(orders[["customer_id"]].drop_duplicates(),
                       on="customer_id", how="left", indicator=True)
never = both[both["_merge"] == "left_only"]
print(len(never))
print(never.sort_values("joined", ascending=False)
      [["customer_id", "tier", "joined"]].head())

# %% Exercise 13.2
full = orders.merge(customers, on="customer_id", how="left",
                    validate="many_to_one")
full["tier"] = full["tier"].fillna("unknown")
print(full["tier"].value_counts())

# %% Exercise 13.3
stats = orders.groupby("customer_id").agg(
    orders=("order_id", "count"), first_order=("order_date", "min"))
profile = customers.merge(stats, left_on="customer_id",
                          right_index=True, how="left",
                          validate="one_to_one")
profile["orders"] = profile["orders"].fillna(0).astype(int)
print(len(profile) == len(customers))
print(profile.sort_values("orders", ascending=False).head(3))

# %% Exercise 13.4
linked = tickets.merge(orders[["order_id", "status"]], on="order_id",
                       how="inner", validate="many_to_one")
cancelled = linked[linked["status"] == "cancelled"]
print(len(cancelled), "tickets about cancelled orders")
template = (cancelled["subject"].str.strip().str.lower()
            .str.replace(r"#?hc[-\s]?\d{5}", "…", regex=True))
print(template.value_counts())

# %% Exercise 13.5
files = sorted(Path(".").glob("orders_2026-*.csv"))
parts = [pd.read_csv(f) for f in files]
parts[2] = parts[2].rename(columns={"quantity": "qty"})
broken = pd.concat(parts, ignore_index=True)
print(broken[["quantity", "qty"]].isna().sum())


def check_columns(frames, names):
    expected = list(frames[0].columns)
    for frame, name in zip(frames, names):
        if list(frame.columns) != expected:
            diff = set(frame.columns) ^ set(expected)
            raise ValueError(f"{name}: columns differ: {sorted(diff)}")


try:
    check_columns(parts, [f.name for f in files])
except ValueError as err:
    print(err)

# %% Exercise 13.6
con = sqlite3.connect("data/chinook.sqlite")
q = lambda sql: pd.read_sql_query(sql, con)
sales = (q("SELECT InvoiceId, TrackId, UnitPrice, Quantity "
           "FROM InvoiceLine")
         .merge(q("SELECT InvoiceId, CustomerId FROM Invoice"),
                on="InvoiceId", validate="many_to_one")
         .merge(q("SELECT CustomerId, Country FROM Customer"),
                on="CustomerId", validate="many_to_one")
         .merge(q("SELECT TrackId, GenreId FROM Track"),
                on="TrackId", validate="many_to_one")
         .merge(q("SELECT GenreId, Name AS genre FROM Genre"),
                on="GenreId", validate="many_to_one"))
sales["revenue"] = sales["UnitPrice"] * sales["Quantity"]
by = sales.groupby(["Country", "genre"])["revenue"].sum()
top = by.sort_values(ascending=False).groupby(level="Country").head(1)
print(top.sort_values(ascending=False).head(5))

# %% Exercise 13.7
def safe_merge(left, right, **kwargs):
    out = left.merge(right, indicator=True, **kwargs)
    counts = out["_merge"].value_counts()
    print(", ".join(f"{k}: {v}" for k, v in counts.items()))
    if kwargs.get("how") == "left" and len(out) != len(left):
        raise ValueError(f"left join changed rows: {len(left)} -> "
                         f"{len(out)}")
    return out.drop(columns="_merge")


ok = safe_merge(orders, customers, on="customer_id", how="left")
dup = pd.concat([customers, customers.iloc[[5]]])
try:
    safe_merge(orders, dup, on="customer_id", how="left")
except ValueError as err:
    print("ValueError:", err)

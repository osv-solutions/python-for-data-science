"""Chapter 13: Combining Data

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch13_combining.py

or open the notebook and run the cells in order.
"""

# %% 13.1 Tables and keys
import pandas as pd

orders = pd.read_parquet("data/shop_orders.parquet")
customers = pd.read_csv("data/shop_customers.csv",
                        parse_dates=["joined"])
print(len(orders), "orders,", len(customers), "customers")
print(customers.head(3))
print(customers["customer_id"].is_unique)

# %% 13.2 Merging two tables
both = orders.merge(customers, on="customer_id")
print(both.shape)
print(both[["order_id", "customer_id", "name", "tier"]].head(3))

# %% 13.3 Join types
check = orders.merge(customers, on="customer_id", how="outer",
                     indicator=True)
print(check["_merge"].value_counts())
lost = check.loc[check["_merge"] == "left_only", "customer_id"]
print(lost.value_counts())

# %% 13.3 Join types
full = orders.merge(customers, on="customer_id", how="left")
print(len(full), full["tier"].isna().sum(), "orders without a tier")
print(full.groupby("tier", dropna=False)["order_id"].count())

# %% 13.4 Keys that don't match
tickets = pd.read_csv("data/support_tickets.csv")
pattern = r"(?i)#?\bhc[-\s]?(\d{5})"
tickets["order_no"] = tickets["subject"].str.extract(pattern)[0]
naive = tickets.merge(orders, left_on="order_no",
                      right_on="order_id")
print(len(naive), "matches")

# %% 13.4 Keys that don't match
orders["order_no"] = orders["order_id"].str[3:].astype(int)
try:
    tickets.merge(orders, on="order_no")
except ValueError as err:
    print("ValueError:", str(err)[:60])

# %% 13.4 Keys that don't match
tickets["order_id"] = "HC-" + tickets["order_no"]
linked = tickets.merge(orders, on="order_id", how="left",
                       indicator=True)
print(linked["_merge"].value_counts())

# %% 13.5 Catching bad joins with validate
messy = pd.concat([customers, customers.iloc[[5]]])
dup = messy["customer_id"].iloc[-1]
grown = orders.merge(messy, on="customer_id", how="left")
print(dup, "->", len(orders), "orders became", len(grown), "rows")

# %% 13.5 Catching bad joins with validate
try:
    orders.merge(messy, on="customer_id", how="left",
                 validate="many_to_one")
except pd.errors.MergeError as err:
    print("MergeError:", str(err).split(";")[0])

# %% 13.6 Stacking tables with concat
for month, part in orders.groupby(orders["order_date"]
                                  .dt.to_period("M")):
    part.to_csv(f"orders_{month}.csv", index=False)
from pathlib import Path

files = sorted(Path(".").glob("orders_2026-*.csv"))
print([f.name for f in files][:3], len(files), "files")

# %% 13.6 Stacking tables with concat
monthly = [pd.read_csv(f).assign(source=f.name) for f in files]
stacked = pd.concat(monthly, ignore_index=True)
print(stacked.shape)
print(stacked["source"].value_counts().sort_index().head(3))

# %% 13.6 Stacking tables with concat
extra = pd.DataFrame({"order_id": ["HC-20001"],
                      "coupon": ["SPRING10"]})
combined = pd.concat([stacked, extra], ignore_index=True)
print(combined.shape)
print(combined[["order_id", "status", "coupon"]].tail(2))

# %% 13.7 Joining on the index
tiers = customers.set_index("customer_id")["tier"]
with_tier = orders.join(tiers, on="customer_id")
print(with_tier["tier"].value_counts(dropna=False))

# %% 13.8 Putting it together: do slow deliveries cause complaints?
topic = tickets["subject"].str.contains(r"(?i)damaged|where is|"
                                        r"not here")
complaints = tickets.loc[topic & tickets["order_id"].notna(),
                         ["ticket_id", "order_id"]]
per_order = (complaints.groupby("order_id").size()
             .rename("complaints"))
print(len(complaints), "complaints about", len(per_order), "orders")

# %% 13.8 Putting it together: do slow deliveries cause complaints?
delivered = orders[orders["status"] == "delivered"]
result = delivered.merge(per_order, left_on="order_id",
                         right_index=True, how="left",
                         validate="one_to_one")
result["complaints"] = result["complaints"].fillna(0)
print(len(delivered) == len(result))
share = result.groupby("shipping_days")["complaints"].apply(
    lambda c: (c > 0).mean())
print((share * 100).round(1))

# %% 13.8 Putting it together: do slow deliveries cause complaints?
import sqlite3

con = sqlite3.connect("data/chinook.sqlite")
lines = pd.read_sql_query("SELECT * FROM InvoiceLine", con)
tracks = pd.read_sql_query("SELECT TrackId, GenreId FROM Track", con)
genres = pd.read_sql_query("SELECT GenreId, Name FROM Genre", con)
sales = (lines.merge(tracks, on="TrackId", validate="many_to_one")
              .merge(genres, on="GenreId", validate="many_to_one"))
sales["revenue"] = sales["UnitPrice"] * sales["Quantity"]
print(len(lines) == len(sales))
print(sales.groupby("Name")["revenue"].sum().nlargest(3))

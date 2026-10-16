"""Chapter 14: Grouping, Aggregating and Reshaping

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch14_grouping.py

or open the notebook and run the cells in order.
"""

# %% 14.1 Split, apply, combine
import pandas as pd

orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].copy()
orders["revenue"] = orders["quantity"] * orders["unit_price"]
orders["month"] = orders["order_date"].dt.to_period("M")
print(len(orders), "orders,", f"${orders['revenue'].sum():,.2f}")

# %% 14.1 Split, apply, combine
by_product = orders.groupby("product")["revenue"].sum()
print(by_product.sort_values(ascending=False).round(2))

# %% 14.1 Split, apply, combine
by_two = orders.groupby(["state", "bag_size"])["revenue"].sum()
print(by_two.head(4).round(2))
print(by_two.loc["PA"].round(2))

# %% 14.1 Split, apply, combine
g = orders.groupby("product")
print(pd.DataFrame({"rows": g.size(), "rated": g["rating"].count()}))

# %% 14.2 Several summaries with agg
summary = orders.groupby("product").agg(
    orders=("order_id", "count"),
    revenue=("revenue", "sum"),
    avg_bags=("quantity", "mean"),
    rating=("rating", "mean"),
)
print(summary.round(2).sort_values("revenue", ascending=False))

# %% 14.2 Several summaries with agg
def share_1kg(sizes):
    return (sizes == "1kg").mean()


per_state = orders.groupby("state").agg(
    customers=("customer_id", "nunique"),
    big_bags=("bag_size", share_1kg),
    slow=("shipping_days", lambda d: (d >= 6).mean()),
)
print(per_state.round(2).sort_values("slow"))

# %% 14.3 transform: group results on every row
orders["product_avg"] = (orders.groupby("product")["revenue"]
                         .transform("mean"))
orders["vs_avg"] = orders["revenue"] - orders["product_avg"]
cols = ["order_id", "product", "revenue", "product_avg", "vs_avg"]
print(orders[cols].head(3).round(2))

# %% 14.3 transform: group results on every row
state_total = orders.groupby("state")["revenue"].transform("sum")
orders["share_of_state"] = orders["revenue"] / state_total
top = orders.nlargest(3, "share_of_state")
cols = ["order_id", "state", "revenue", "share_of_state"]
print(top[cols].round(3))

# %% 14.3 transform: group results on every row
fill = (orders.groupby(["product", "bag_size"])["unit_price"]
        .transform("median"))
filled = orders["unit_price"].fillna(fill)
print(orders["unit_price"].isna().sum(), "->", filled.isna().sum())

# %% 14.3 transform: group results on every row
loyal = orders.groupby("customer_id").filter(lambda g: len(g) >= 5)
print(loyal["customer_id"].nunique(), "customers,", len(loyal),
      "orders")

# %% 14.4 Pivot tables and crosstabs
grid = orders.pivot_table(index="state", columns="month",
                          values="revenue", aggfunc="sum",
                          margins=True, margins_name="Total")
print(grid.round(0))

# %% 14.4 Pivot tables and crosstabs
mix = pd.crosstab(orders["product"], orders["bag_size"],
                  normalize="index")
print((mix * 100).round(1))

# %% 14.5 Long and wide: melt and pivot
gap = pd.read_csv("data/gapminder.csv")
long = gap[["country", "continent", "year", "lifeExp"]]
print(long.head(3))

# %% 14.5 Long and wide: melt and pivot
wide = long.pivot(index="country", columns="year", values="lifeExp")
print(wide.shape)
print(wide.loc[["Japan", "Brazil", "Nigeria"], [1952, 1982, 2007]])

# %% 14.5 Long and wide: melt and pivot
back = wide.reset_index().melt(id_vars="country", var_name="year",
                               value_name="lifeExp")
print(back.shape)
print(back.sort_values(["country", "year"]).head(3))

# %% 14.6 Running totals, changes and ranks
daily = orders.groupby("order_date")["revenue"].sum()
daily = daily.asfreq("D", fill_value=0)
print(len(daily), "days")
print(daily.cumsum().iloc[[30, 89, -1]].round(0))

# %% 14.6 Running totals, changes and ranks
week = daily.rolling(7).mean()
print(week.round(1).iloc[[6, 7, 8]])
print(f"best week ending {week.idxmax().date()}: ${week.max():.0f}")

# %% 14.6 Running totals, changes and ranks
long = long.sort_values(["country", "year"])
long["gain"] = long.groupby("country")["lifeExp"].diff()
print(long[long["country"] == "Cambodia"][["year", "lifeExp",
                                           "gain"]].iloc[4:8])

# %% 14.6 Running totals, changes and ranks
y2007 = long[long["year"] == 2007].copy()
y2007["rank"] = (y2007.groupby("continent")["lifeExp"]
                 .rank(ascending=False, method="min").astype(int))
top = y2007[y2007["rank"] == 1]
print(top[["continent", "country", "lifeExp"]])

# %% 14.7 Putting it together: a monthly product report
monthly = (orders.groupby(["month", "product"], as_index=False)
                 ["revenue"].sum())
monthly["change"] = (monthly.sort_values("month")
                     .groupby("product")["revenue"].pct_change())
monthly["rank"] = (monthly.groupby("month")["revenue"]
                   .rank(ascending=False).astype(int))
print(monthly[monthly["month"] == "2026-06"].sort_values("rank")
      .round(2))

# %% 14.7 Putting it together: a monthly product report
ranks = monthly.pivot(index="product", columns="month", values="rank")
print(ranks)

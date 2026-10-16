"""Solutions to the Chapter 14 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch14_solutions.py

The explanations are in ch14_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import pandas as pd

orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].copy()
orders["revenue"] = orders["quantity"] * orders["unit_price"]
orders["month"] = orders["order_date"].dt.to_period("M")
gap = pd.read_csv("data/gapminder.csv")

# %% Exercise 14.1
penguins = pd.read_csv("data/penguins.csv")
table = penguins.groupby(["species", "sex"], as_index=False).agg(
    birds=("body_mass_g", "size"), mass_g=("body_mass_g", "mean"))
print(table.round(0))

# %% Exercise 14.2
best = orders.groupby("customer_id").agg(
    revenue=("revenue", "sum"), orders=("order_id", "count"))
print(best.nlargest(10, "revenue").round(2))

# %% Exercise 14.3
total = orders.groupby("customer_id")["revenue"].transform("sum")
orders["share"] = orders["revenue"] / total
big = orders[orders["share"] > 0.5]
print(big["customer_id"].nunique(), "customers")
print(big.nlargest(3, "share")[["customer_id", "revenue", "share"]])

# %% Exercise 14.4
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday"]
orders["weekday"] = pd.Categorical(
    orders["order_date"].dt.day_name(), categories=days, ordered=True)
counts = orders.pivot_table(index="weekday", columns="bag_size",
                            values="order_id", aggfunc="count",
                            margins=True, observed=True)
print(counts)
share = counts["1kg"] / counts["All"]
print(share.drop("All").idxmax(), f"{share.drop('All').max():.0%}")

# %% Exercise 14.5
gap["weighted"] = gap["lifeExp"] * gap["pop"]
sums = gap.groupby(["continent", "year"])[["weighted", "pop"]].sum()
sums["lifeExp"] = sums["weighted"] / sums["pop"]
wide = sums["lifeExp"].unstack("year")
print(wide[[1952, 1982, 2007]].round(1))

# %% Exercise 14.6
ends = gap[gap["year"].isin([1952, 2007])].pivot(
    index=["continent", "country"], columns="year", values="gdpPercap")
ends["growth"] = ends[2007] / ends[1952]
ends["rank"] = (ends.groupby("continent")["growth"]
                .rank(ascending=False).astype(int))
print(ends[ends["rank"] == 1].round(1))

# %% Exercise 14.7
sales = pd.read_excel("data/store_sales.xlsx", sheet_name="Orders",
                      header=2)
sales["revenue"] = sales["units"] * sales["unit_price"]
sales["week"] = sales["order_date"].dt.to_period("W").dt.start_time
weekly = sales.pivot_table(index="week", columns="region",
                           values="revenue", aggfunc="sum",
                           fill_value=0)
smooth = weekly.rolling(4).mean()
print(weekly.idxmax(axis=1).value_counts())
long = weekly.reset_index().melt(id_vars="week", var_name="region",
                                 value_name="revenue")
print(long.shape)
print(smooth.dropna().round(0).head(3))

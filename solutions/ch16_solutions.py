"""Solutions to the Chapter 16 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch16_solutions.py

The explanations are in ch16_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", palette="colorblind")
penguins = pd.read_csv("data/penguins.csv")
gap = pd.read_csv("data/gapminder.csv")
orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].assign(
    revenue=lambda d: d["quantity"] * d["unit_price"])

# %% Exercise 16.1
sns.histplot(data=penguins, x="bill_length_mm", hue="sex",
             element="step", bins=30)
plt.show()

# %% Exercise 16.2
fig, ax = plt.subplots(figsize=(6, 3))
sns.boxplot(data=orders, x="bag_size", y="revenue",
            order=["250g", "500g", "1kg"], ax=ax)
ax.set_yscale("log")
plt.show()

# %% Exercise 16.3
two = gap[gap["year"].isin([1952, 2007])]
g = sns.relplot(data=two, x="gdpPercap", y="lifeExp", hue="continent",
                col="year", height=3, aspect=1.1, s=18)
g.set(xscale="log")
g.set_axis_labels("GDP per person ($, log)", "Life expectancy")
plt.show()

# %% Exercise 16.4
raw = pd.read_csv("data/support_tickets.csv")
iso = raw["channel"].isin(["web", "phone"])
opened = pd.concat([
    pd.to_datetime(raw.loc[iso, "opened"], format="ISO8601", utc=True),
    pd.to_datetime(raw.loc[~iso, "opened"], format="%m/%d/%Y %I:%M %p")
    .dt.tz_localize("America/New_York").dt.tz_convert("UTC"),
]).sort_index().dt.tz_convert("America/New_York")
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
grid = pd.crosstab(opened.dt.dayofweek.map(dict(enumerate(days))),
                   opened.dt.hour).reindex(days)
fig, ax = plt.subplots(figsize=(7, 2.8))
sns.heatmap(grid, cmap="Blues", cbar_kws={"label": "tickets"}, ax=ax)
ax.set_xlabel("Hour (New York)")
ax.set_ylabel("")
plt.show()

# %% Exercise 16.5
rated = orders.dropna(subset=["rating", "shipping_days"]).astype(
    {"rating": float, "shipping_days": int})
g = sns.catplot(data=rated, x="shipping_days", y="rating",
                col="bag_size", col_order=["250g", "500g", "1kg"],
                kind="point", height=2.8, aspect=0.9)
g.set_axis_labels("Days to deliver", "Mean rating")
plt.show()

# %% Exercise 16.6
fig, ax = plt.subplots(figsize=(6, 3))
sns.pointplot(data=penguins, x="species", y="bill_length_mm",
              hue="sex", dodge=0.3, ax=ax)
ax.set_ylabel("Mean bill length (mm)")
plt.show()

# %% Exercise 16.7
num = ["bill_length_mm", "bill_depth_mm", "flipper_length_mm",
       "body_mass_g"]
overall = penguins[num].corr()
within = penguins.groupby("species")[num].corr().groupby(level=1).mean()
diff = (within - overall).loc[num, num]
short = ["bill_len", "bill_dep", "flipper", "mass"]
print(diff.set_axis(short, axis=0).set_axis(short, axis=1).round(2))

# %% Exercise 16.7
g = sns.lmplot(data=penguins, x="flipper_length_mm",
               y="bill_depth_mm", hue="species", height=3.2,
               aspect=1.6, scatter_kws={"s": 10, "alpha": 0.6})
r = penguins["flipper_length_mm"].corr(penguins["bill_depth_mm"])
print(f"overall r = {r:.2f}")
plt.show()

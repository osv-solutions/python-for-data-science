"""Chapter 15: Visualization with Matplotlib

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch15_matplotlib.py

or open the notebook and run the cells in order.
"""

# %% 15.1 Figures and axes
import matplotlib.pyplot as plt
import pandas as pd

years = [2021, 2022, 2023, 2024, 2025]
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(years, [12, 15, 14, 19, 23])
ax.set_xticks(years)
ax.set_title("Average orders per day")
ax.set_xlabel("Year")
ax.set_ylabel("Orders")
plt.show()

# %% 15.1 Figures and axes
plt.rcParams.update({"axes.spines.top": False,
                     "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.3,
                     "legend.frameon": False})

# %% 15.2 Line charts: change over time
gap = pd.read_csv("data/gapminder.csv")
four = ["Japan", "Brazil", "India", "Nigeria"]
wide = (gap[gap["country"].isin(four)]
        .pivot(index="year", columns="country", values="lifeExp"))
fig, ax = plt.subplots(figsize=(6, 3.4))
for country in four:
    ax.plot(wide.index, wide[country], marker="o", markersize=3,
            label=country)
ax.set_ylabel("Life expectancy (years)")
ax.legend(loc="lower right")
plt.show()

# %% 15.2 Line charts: change over time
fig, ax = plt.subplots(figsize=(6, 3.4))
for country in four:
    line, = ax.plot(wide.index, wide[country], lw=2)
    ax.text(2008.5, wide[country].iloc[-1], country,
            color=line.get_color(), va="center", fontsize=9)
ax.set_xlim(1950, 2016)
ax.set_ylabel("Life expectancy (years)")
ax.set_title("Japan gained 20 years, Nigeria 10")
plt.show()

# %% 15.3 Bar charts: comparing categories
orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"]
revenue = (orders["quantity"] * orders["unit_price"]).groupby(
    orders["product"]).sum().sort_values()
fig, ax = plt.subplots(figsize=(6, 3))
bars = ax.barh(revenue.index, revenue.values, color="#2a9bb0")
ax.bar_label(bars, fmt="${:,.0f}", padding=3, fontsize=8)
ax.set_xlabel("Revenue, January to June 2026")
ax.grid(axis="y", visible=False)
plt.show()

# %% 15.3 Bar charts: comparing categories
import numpy as np

months = orders.assign(month=orders["order_date"].dt.month)
two = months[months["month"].isin([1, 6])].pivot_table(
    index="product", columns="month", values="quantity",
    aggfunc="sum").sort_values(6)
y = np.arange(len(two))
fig, ax = plt.subplots(figsize=(6, 3.2))
ax.barh(y - 0.2, two[1], height=0.4, label="January")
ax.barh(y + 0.2, two[6], height=0.4, label="June")
ax.set_yticks(y, two.index)
ax.set_xlabel("Bags sold")
ax.legend()
plt.show()

# %% 15.4 Scatter charts: relationships
y2007 = gap[gap["year"] == 2007]
fig, ax = plt.subplots(figsize=(6, 3.6))
ax.scatter(y2007["gdpPercap"], y2007["lifeExp"],
           s=y2007["pop"] / 4e6, alpha=0.5, color="#1d5c8c",
           edgecolor="white", linewidth=0.5)
ax.set_xscale("log")
ax.set_xlabel("GDP per person (US$, log scale)")
ax.set_ylabel("Life expectancy (years)")
for name in ["China", "India", "United States", "South Africa"]:
    row = y2007[y2007["country"] == name].iloc[0]
    ax.annotate(name, (row["gdpPercap"], row["lifeExp"]),
                xytext=(6, -10), textcoords="offset points",
                fontsize=8)
plt.show()

# %% 15.5 Histograms: distributions
penguins = pd.read_csv("data/penguins.csv")
mass = penguins["body_mass_g"].dropna()
fig, ax = plt.subplots(figsize=(6, 3))
ax.hist(mass, bins=25, color="#2a9bb0", edgecolor="white")
ax.axvline(mass.median(), color="#c0582b", lw=1.5, ls="--")
ax.text(mass.median() + 40, 30, f"median {mass.median():,.0f} g",
        color="#c0582b", fontsize=8)
ax.set_xlabel("Body mass (g)")
ax.set_ylabel("Penguins")
plt.show()

# %% 15.6 Several charts in one figure
fig, axes = plt.subplots(1, 3, figsize=(7, 2.6), sharey=True)
for ax, bins in zip(axes, [6, 25, 120]):
    ax.hist(mass, bins=bins, color="#2a9bb0", edgecolor="white",
            linewidth=0.3)
    ax.set_title(f"{bins} bins", fontsize=9)
    ax.set_xlabel("Body mass (g)")
axes[0].set_ylabel("Penguins")
fig.tight_layout()
plt.show()

# %% 15.6 Several charts in one figure
species = ["Adelie", "Chinstrap", "Gentoo"]
fig, axes = plt.subplots(3, 1, figsize=(6, 4.2), sharex=True)
for ax, name in zip(axes, species):
    data = penguins.loc[penguins["species"] == name, "body_mass_g"]
    ax.hist(data.dropna(), bins=20, color="#1d5c8c",
            edgecolor="white")
    ax.set_title(name, fontsize=9, loc="left")
    ax.set_yticks([])
axes[-1].set_xlabel("Body mass (g)")
fig.tight_layout()
plt.show()

# %% 15.7 Saving charts
fig, ax = plt.subplots(figsize=(6, 3))
ax.barh(revenue.index, revenue.values, color="#2a9bb0")
ax.set_xlabel("Revenue ($)")
fig.savefig("revenue.png", dpi=300, bbox_inches="tight")
fig.savefig("revenue.svg", bbox_inches="tight")
plt.close(fig)
from pathlib import Path

for name in ["revenue.png", "revenue.svg"]:
    print(f"{name:<12} {Path(name).stat().st_size:>8,} bytes")

# %% 15.8 Quick charts with pandas
monthly = (orders.assign(revenue=orders["quantity"]
                         * orders["unit_price"])
           .groupby(orders["order_date"].dt.to_period("M"))
           ["revenue"].sum())
ax = monthly.plot(kind="bar", figsize=(6, 2.8), color="#1d5c8c",
                  rot=0)
ax.set_xlabel("")
ax.set_ylabel("Revenue ($)")
plt.show()

# %% 15.9 Putting it together: a one-page summary
rated = orders.dropna(subset=["rating", "shipping_days"])
stars = rated.groupby("shipping_days")["rating"].mean()
mix = orders["bag_size"].value_counts(normalize=True)[
    ["250g", "500g", "1kg"]]
print(stars.round(2).tolist())
print((mix * 100).round(1).tolist())

# %% 15.9 Putting it together: a one-page summary
fig, axes = plt.subplots(2, 2, figsize=(7, 5))
axes[0, 0].plot(monthly.index.strftime("%b"), monthly.values,
                marker="o", color="#1d5c8c")
axes[0, 0].set_title("Revenue per month ($)")
axes[0, 1].barh(revenue.index, revenue.values, color="#2a9bb0")
axes[0, 1].set_title("Revenue by product ($)")
axes[1, 0].bar(stars.index.astype(str), stars.values,
               color="#c0582b")
axes[1, 0].set_title("Rating by days to deliver")
axes[1, 1].bar(mix.index, mix.values * 100, color="#2e7d4f")
axes[1, 1].set_title("Orders by bag size (%)")
fig.suptitle("Hilltop Coffee Roasters, January to June 2026")
fig.tight_layout()
fig.savefig("summary.png", dpi=300)
plt.show()

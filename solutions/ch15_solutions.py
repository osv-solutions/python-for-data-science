"""Solutions to the Chapter 15 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch15_solutions.py

The explanations are in ch15_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

gap = pd.read_csv("data/gapminder.csv")
penguins = pd.read_csv("data/penguins.csv")
orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"]

# %% Exercise 15.1
world = gap.groupby("year")["pop"].sum() / 1e9
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(world.index, world.values, marker="o", markersize=3)
ax.set_xticks(world.index[::2])
ax.set_ylim(0, None)
ax.set_xlabel("Year")
ax.set_ylabel("Population (billions)")
ax.set_title(f"Population of 142 countries: {world.iloc[0]:.1f} to "
             f"{world.iloc[-1]:.1f} billion")
plt.show()

# %% Exercise 15.2
counts = penguins["island"].value_counts().sort_values()
fig, ax = plt.subplots(figsize=(5, 2.2))
bars = ax.barh(counts.index, counts.values, color="#2a9bb0")
ax.bar_label(bars, padding=3)
ax.set_xticks([])
ax.grid(False)
ax.set_title("Penguins per island")
plt.show()

# %% Exercise 15.3
fig, ax = plt.subplots(figsize=(6, 3.4))
for (name, group), marker in zip(penguins.groupby("species"), "os^"):
    ax.scatter(group["bill_length_mm"], group["bill_depth_mm"], s=14,
               marker=marker, label=name, alpha=0.7)
ax.set_xlabel("Bill length (mm)")
ax.set_ylabel("Bill depth (mm)")
ax.legend()
plt.show()

# %% Exercise 15.4
stats = gap.groupby(["continent", "year"])["lifeExp"].agg(
    ["min", "median", "max"])
continents = stats.index.get_level_values(0).unique()
fig, axes = plt.subplots(1, 5, figsize=(7.2, 2.4), sharey=True)
for ax, name in zip(axes, continents):
    s = stats.loc[name]
    ax.fill_between(s.index, s["min"], s["max"], alpha=0.25,
                    color="#2a9bb0")
    ax.plot(s.index, s["median"], color="#1d5c8c")
    ax.set_title(name, fontsize=9)
    ax.set_xticks([1960, 2000])
axes[0].set_ylabel("Life expectancy (years)")
fig.tight_layout()
plt.show()

# %% Exercise 15.5
days = orders["shipping_days"].dropna().astype(int)
slow = (days >= 6).mean()
fig, ax = plt.subplots(figsize=(6, 2.8))
ax.hist(days, bins=np.arange(days.min(), days.max() + 2) - 0.5,
        color="#2a9bb0", edgecolor="white")
ax.set_xticks(range(days.min(), days.max() + 1))
ax.set_xlabel("Days to deliver")
ax.set_ylabel("Orders")
ax.set_title(f"{slow:.0%} of deliveries took six days or more")
plt.show()

# %% Exercise 15.6
fig, ax = plt.subplots(figsize=(6, 3.4))
for (name, group), marker in zip(penguins.groupby("species"), "os^"):
    ax.scatter(group["bill_length_mm"], group["bill_depth_mm"], s=14,
               marker=marker, label=name, alpha=0.7)
ax.legend()
for ext in ["png", "svg", "pdf"]:
    fig.savefig(f"bills.{ext}", dpi=300, bbox_inches="tight")
    print(f"bills.{ext}  {Path(f'bills.{ext}').stat().st_size:>9,} "
          "bytes")
plt.close(fig)

# %% Exercise 15.7
def bar_chart(series, title, color="#2a9bb0", fmt="{:,.0f}"):
    data = series.sort_values()
    fig, ax = plt.subplots(figsize=(5.5, 0.35 * len(data) + 0.8))
    bars = ax.barh(data.index.astype(str), data.values, color=color)
    ax.bar_label(bars, fmt=fmt, padding=3, fontsize=8)
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_title(title, loc="left")
    return fig


revenue = orders["quantity"] * orders["unit_price"]
bar_chart(revenue.groupby(orders["product"]).sum(),
          "Revenue by product ($)")
bar_chart(revenue.groupby(orders["state"]).sum(), "Revenue by state ($)",
          color="#1d5c8c")
plt.show()

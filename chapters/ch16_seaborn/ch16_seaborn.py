"""Chapter 16: Statistical Charts with seaborn

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch16_seaborn.py

or open the notebook and run the cells in order.
"""

# %% 16.1 Columns to pictures
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", palette="colorblind")
penguins = pd.read_csv("data/penguins.csv")
sns.scatterplot(data=penguins, x="flipper_length_mm",
                y="body_mass_g", hue="species")
plt.show()

# %% 16.2 Distributions
sns.histplot(data=penguins, x="body_mass_g", hue="species",
             element="step", bins=25)
plt.show()

# %% 16.2 Distributions
sns.kdeplot(data=penguins, x="body_mass_g", hue="species",
            fill=True, common_norm=False, alpha=0.3)
plt.show()

# %% 16.2 Distributions
fig, axes = plt.subplots(1, 2, figsize=(7, 3), sharey=True)
sns.boxplot(data=penguins, x="species", y="body_mass_g",
            hue="species", ax=axes[0])
sns.violinplot(data=penguins, x="species", y="body_mass_g",
               hue="species", inner="quart", ax=axes[1])
axes[0].set_title("Box plot")
axes[1].set_title("Violin plot")
plt.show()

# %% 16.3 Relationships
gentoo = penguins[penguins["species"] == "Gentoo"]
fig, ax = plt.subplots(figsize=(6, 3.2))
sns.regplot(data=gentoo, x="flipper_length_mm", y="body_mass_g",
            scatter_kws={"s": 12, "alpha": 0.6}, ax=ax)
ax.set_title("Gentoo: each millimeter of flipper adds ~55 g")
plt.show()

# %% 16.3 Relationships
import numpy as np

both = gentoo.dropna(subset=["flipper_length_mm", "body_mass_g"])
slope, intercept = np.polyfit(both["flipper_length_mm"],
                              both["body_mass_g"], 1)
print(f"slope {slope:.1f} g per mm, intercept {intercept:,.0f} g")

# %% 16.3 Relationships
gap = pd.read_csv("data/gapminder.csv")
fig, ax = plt.subplots(figsize=(6, 3.4))
sns.lineplot(data=gap, x="year", y="lifeExp", hue="continent",
             style="continent", markers=True, dashes=False, ax=ax)
ax.set_ylabel("Life expectancy (years)")
ax.legend(fontsize=8, ncols=2)
plt.show()

# %% 16.4 Categorical charts
fig, axes = plt.subplots(1, 2, figsize=(7, 3.4))
sns.countplot(data=penguins, x="island", hue="species", ax=axes[0])
sns.barplot(data=penguins, x="species", y="bill_length_mm",
            hue="sex", ax=axes[1])
axes[0].set_title("Penguins per island")
axes[1].set_title("Mean bill length (mm)")
for ax in axes:
    sns.move_legend(ax, "upper center", bbox_to_anchor=(0.5, -0.32),
                    ncols=3, title=None)
fig.tight_layout()
plt.show()

# %% 16.4 Categorical charts
fig, ax = plt.subplots(figsize=(6, 3))
sns.boxplot(data=penguins, x="species", y="bill_depth_mm",
            color="white", fliersize=0, ax=ax)
sns.stripplot(data=penguins, x="species", y="bill_depth_mm",
              hue="sex", dodge=True, size=3, alpha=0.7, ax=ax)
plt.show()

# %% 16.5 Heatmaps
orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].assign(
    revenue=lambda d: d["quantity"] * d["unit_price"],
    month=lambda d: d["order_date"].dt.strftime("%b"))
grid = orders.pivot_table(index="product", columns="month",
                          values="revenue", aggfunc="sum")
grid = grid[["Jan", "Feb", "Mar", "Apr", "May", "Jun"]].astype(float)
fig, ax = plt.subplots(figsize=(6.4, 3))
sns.heatmap(grid, annot=True, fmt=",.0f", cmap="Blues",
            linewidths=1, cbar=False, annot_kws={"size": 8}, ax=ax)
ax.set_xlabel("")
ax.set_ylabel("")
plt.show()

# %% 16.6 Facets: one chart per group
g = sns.displot(data=penguins, x="flipper_length_mm", col="species",
                hue="sex", height=2.6, aspect=0.9, bins=15)
g.set_axis_labels("Flipper length (mm)", "Penguins")
g.set_titles("{col_name}")
plt.show()

# %% 16.7 Themes, palettes and finishing touches
for name in ["colorblind", "Blues", "RdBu"]:
    colors = sns.color_palette(name, 5)
    print(f"{name:<11}", " ".join(c for c in colors.as_hex()))

# %% 16.8 Putting it together: the penguin overview
short = {"bill_length_mm": "bill length", "bill_depth_mm":
         "bill depth", "flipper_length_mm": "flipper",
         "body_mass_g": "mass"}
data = penguins.rename(columns=short)[[*short.values(), "species"]]
g = sns.pairplot(data, hue="species", height=1.6,
                 plot_kws={"s": 10, "alpha": 0.6},
                 diag_kind="kde", corner=True)
plt.show()

# %% 16.8 Putting it together: the penguin overview
g = sns.lmplot(data=penguins, x="bill_length_mm", y="bill_depth_mm",
               hue="species", height=3.2, aspect=1.6,
               scatter_kws={"s": 10, "alpha": 0.6})
g.set_axis_labels("Bill length (mm)", "Bill depth (mm)")
r_all = penguins["bill_length_mm"].corr(penguins["bill_depth_mm"])
print(f"all penguins: r = {r_all:.2f}")
plt.show()

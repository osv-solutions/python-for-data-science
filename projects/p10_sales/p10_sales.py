"""Project 10 (Intermediate): Sales Performance Report

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p10_sales.py

or open the notebook and run the cells in order.
"""

# %% Step 2: Meet the database
import textwrap

import pandas as pd
from sqlalchemy import create_engine, inspect, text

engine = create_engine("sqlite:///data/trailhead.sqlite")
for table in inspect(engine).get_table_names():
    columns = [c["name"] for c in inspect(engine).get_columns(table)]
    print(f"{table:<12}", ", ".join(columns))

# %% Step 2: Meet the database
def sql(query, **params):
    with engine.connect() as con:
        return pd.read_sql(text(query), con, params=params)

print(sql("""SELECT status, COUNT(*) AS orders,
                    MIN(order_date) AS first, MAX(order_date) AS last
             FROM orders GROUP BY status"""))
print(sql("SELECT COUNT(*) AS lines FROM order_lines"))

# %% Step 3: One query for the facts
FACTS = """
SELECT o.order_id, o.order_date, o.rep_id, c.customer_id,
       c.name AS customer, c.kind, c.region, p.category,
       l.quantity * l.unit_price AS revenue,
       l.quantity * p.unit_cost AS cost, l.discount
FROM order_lines AS l
JOIN orders AS o ON o.order_id = l.order_id
JOIN products AS p ON p.product_id = l.product_id
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.status = 'shipped'
  AND o.order_date BETWEEN :first AND :last
"""
sales = sql(FACTS, first="2024-01-01", last="2025-12-31")
sales["order_date"] = pd.to_datetime(sales["order_date"])
sales["year"] = sales["order_date"].dt.year
print(sales.shape)

# %% Step 3: One query for the facts
check = sql("""SELECT SUM(l.quantity * l.unit_price) AS revenue
               FROM order_lines AS l JOIN orders AS o USING (order_id)
               WHERE o.status = 'shipped'""")
print(f"{check.loc[0, 'revenue']:,.2f}")
print(f"{sales['revenue'].sum():,.2f}")
print(sales["order_id"].nunique(), "orders")

# %% Step 4: The key figures
def key_figures(df):
    revenue = df["revenue"].sum()
    return pd.Series({
        "Revenue": revenue,
        "Gross margin": 1 - df["cost"].sum() / revenue,
        "Orders": df["order_id"].nunique(),
        "Customers": df["customer_id"].nunique(),
        "Revenue per order": revenue / df["order_id"].nunique(),
        "Average discount": df["discount"].mean(),
    })

kpi = sales.groupby("year").apply(key_figures).T
kpi["Change"] = kpi[2025] / kpi[2024] - 1
with pd.option_context("display.float_format", "{:,.3f}".format):
    print(kpi)

# %% Step 4: The key figures
formats = {"Revenue": "${:,.0f}", "Gross margin": "{:.1%}",
           "Orders": "{:,.0f}", "Customers": "{:,.0f}",
           "Revenue per order": "${:,.0f}",
           "Average discount": "{:.1%}"}
shares = ["Gross margin", "Average discount"]

def change_text(name):
    if name in shares:
        points = (kpi.loc[name, 2025] - kpi.loc[name, 2024]) * 100
        return f"{points:+.1f} pts"
    return f"{kpi.loc[name, 'Change']:+.1%}"

for name, fmt in formats.items():
    print(f"{name:<18} {fmt.format(kpi.loc[name, 2025]):>12}  "
          f"{change_text(name)}")

# %% Step 5: Trends: months, regions, categories
import matplotlib.pyplot as plt

monthly = sales.pivot_table(index=sales["order_date"].dt.month,
                            columns="year", values="revenue",
                            aggfunc="sum") / 1e6

def monthly_chart(ax):
    ax.plot(monthly.index, monthly[2024], "--", color="#9aa4ae",
            label="2024")
    ax.plot(monthly.index, monthly[2025], "-o", color="#1d5c8c",
            ms=4, label="2025")
    ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    ax.set_ylabel("Revenue ($ millions)")
    ax.set_title("Revenue by month", loc="left", fontsize=10)
    ax.legend(frameon=False)

# %% Step 5: Trends: months, regions, categories
fig, ax = plt.subplots(figsize=(6.4, 2.8))
monthly_chart(ax)
plt.show()

# %% Step 5: Trends: months, regions, categories
by_region = sales.pivot_table(index="region", columns="year",
                              values="revenue", aggfunc="sum")
by_region["change"] = by_region[2025] / by_region[2024] - 1
by_category = sales.pivot_table(index="category", columns="year",
                                values="revenue", aggfunc="sum")
by_category["change"] = by_category[2025] / by_category[2024] - 1
print(by_region.sort_values("change").round(3))
print(by_category["change"].sort_values().round(3))

# %% Step 5: Trends: months, regions, categories
midwest = sales[sales["region"] == "Midwest"].pivot_table(
    index=["customer", "kind"], columns="year", values="revenue",
    aggfunc="sum", fill_value=0)
midwest["change"] = midwest[2025] - midwest[2024]
print(midwest.sort_values("change").head(3).round(0))

# %% Step 5: Trends: months, regions, categories
lost = midwest["change"].idxmin()[0]
last = sales[sales["customer"] == lost]["order_date"].max()
others = midwest.drop(index=lost, level="customer")
rest = others[2025].sum() / others[2024].sum() - 1
print(lost, "- last order", last.date())
print(f"rest of the Midwest: {rest:+.1%}")

# %% Step 5: Trends: months, regions, categories
def region_chart(ax):
    order = by_region.sort_values(2025).index
    y = range(len(order))
    ax.barh([i + 0.2 for i in y], by_region.loc[order, 2024] / 1e6,
            height=0.4, color="#c9d1d9", label="2024")
    ax.barh([i - 0.2 for i in y], by_region.loc[order, 2025] / 1e6,
            height=0.4, color="#1d5c8c", label="2025")
    for i, region in enumerate(order):
        ax.text(by_region.loc[region, [2024, 2025]].max() / 1e6 + 0.2,
                i, f"{by_region.loc[region, 'change']:+.0%}",
                va="center", fontsize=8)
    ax.set_yticks(list(y), order)
    ax.set_xlabel("Revenue ($ millions)")
    ax.set_title("Revenue by region", loc="left", fontsize=10)
    ax.legend(frameon=False, loc="lower right")

# %% Step 5: Trends: months, regions, categories
fig, ax = plt.subplots(figsize=(6.4, 2.6))
region_chart(ax)
plt.show()

# %% Step 6: Sales reps against their targets
targets = sql("SELECT * FROM targets")
reps = sql("SELECT rep_id, name, region, hired FROM reps")
y25 = sales[sales["year"] == 2025].copy()
y25["quarter"] = "2025-Q" + y25["order_date"].dt.quarter.astype(str)
actual = y25.groupby(["rep_id", "quarter"]).agg(
    revenue=("revenue", "sum"), cost=("cost", "sum")).reset_index()
quarters = targets.merge(actual, on=["rep_id", "quarter"], how="left",
                         validate="one_to_one").fillna(0)
print(quarters[quarters["rep_id"] == 6])

# %% Step 6: Sales reps against their targets
scores = quarters.groupby("rep_id")[["target", "revenue",
                                     "cost"]].sum()
scores["attainment"] = scores["revenue"] / scores["target"]
scores["margin"] = 1 - scores["cost"] / scores["revenue"]
scores = reps.set_index("rep_id").join(scores).sort_values(
    "attainment", ascending=False)
print(scores[["name", "region", "attainment", "margin"]].round(3))

# %% Step 6: Sales reps against their targets
print(y25.groupby("rep_id")["discount"].mean().sort_values(
    ascending=False).head(3).round(3))

# %% Step 6: Sales reps against their targets
def rep_chart(ax):
    colors = scores["attainment"].ge(1).map({True: "#2a7f8f",
                                             False: "#c0582b"})
    ax.scatter(scores["attainment"] * 100, scores["margin"] * 100,
               s=scores["revenue"] / 2e4, c=colors, alpha=0.8)
    for row in scores.itertuples():
        ax.annotate(row.name.split()[0], (row.attainment * 100,
                    row.margin * 100), xytext=(4, 3),
                    textcoords="offset points", fontsize=7)
    ax.axvline(100, color="#888888", lw=0.8, ls="--")
    ax.set_xlabel("Target reached (%)")
    ax.set_ylabel("Gross margin (%)")
    ax.set_title("Sales reps, 2025", loc="left", fontsize=10)

# %% Step 6: Sales reps against their targets
fig, ax = plt.subplots(figsize=(6.4, 3.2))
rep_chart(ax)
plt.show()

# %% Step 7: The words
best = by_region["change"].idxmax()
rev = kpi.loc["Revenue"]
margin = kpi.loc["Gross margin", 2025]
gap = (scores["margin"].median() - scores["margin"].min()) * 100
notes = [
    f"Revenue grew {rev['Change']:.0%} to ${rev[2025] / 1e6:.1f}"
    f" million, at a gross margin of {margin:.1%}.",
    f"{best} led with {by_region.loc[best, 'change']:+.0%}. The "
    f"Midwest fell {-by_region.loc['Midwest', 'change']:.0%} after "
    f"{lost} stopped ordering in {last:%B %Y}.",
    f"{(scores['attainment'] >= 1).sum()} of {len(scores)} reps "
    f"reached their target; the highest discounts cost {gap:.0f}"
    " points of margin.",
]
for line in notes:
    print(textwrap.fill(line, 72))

# %% Step 8: Build the PDF
def summary_page():
    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.08, 0.93, "Trailhead Outfitters", fontsize=12,
             color="#1d5c8c")
    fig.text(0.08, 0.89, "Sales performance 2025", fontsize=24,
             weight="bold")
    for i, (name, fmt) in enumerate(formats.items()):
        x, y = 0.08 + (i % 3) * 0.3, 0.78 - (i // 3) * 0.12
        fig.text(x, y, name.upper(), fontsize=8, color="#666666")
        fig.text(x, y - 0.04, fmt.format(kpi.loc[name, 2025]),
                 fontsize=18, weight="bold")
        fig.text(x, y - 0.065, change_text(name) + " vs 2024",
                 fontsize=9, color="#666666")
    for i, line in enumerate(notes):
        fig.text(0.08, 0.48 - i * 0.06, "\u2022  " + line, wrap=True)
    return fig

# %% Step 8: Build the PDF
from matplotlib.backends.backend_pdf import PdfPages

def chart_page(*draws):
    fig, axes = plt.subplots(len(draws), 1, figsize=(8.5, 11),
                             squeeze=False)
    for ax, draw in zip(axes[:, 0], draws):
        draw(ax)
    fig.tight_layout(pad=4)
    return fig

# %% Step 8: Build the PDF
figs = [summary_page(), chart_page(monthly_chart, region_chart),
        chart_page(rep_chart)]
with PdfPages("trailhead_sales_2025.pdf") as pdf:
    for fig in figs:
        pdf.savefig(fig)
        plt.close(fig)
    pdf.infodict()["Title"] = "Sales performance 2025"
    pages = pdf.get_pagecount()
print(pages, "pages")

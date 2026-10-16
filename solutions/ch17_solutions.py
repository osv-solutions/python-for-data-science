"""Solutions to the Chapter 17 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch17_solutions.py

The explanations are in ch17_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px

gap = pd.read_csv("data/gapminder.csv")
y2007 = gap[gap["year"] == 2007]
penguins = pd.read_csv("data/penguins.csv")
orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].assign(
    revenue=lambda d: d["quantity"] * d["unit_price"],
    month=lambda d: d["order_date"].dt.to_period("M").dt.start_time)

# %% Exercise 17.1
fig = px.histogram(penguins, x="body_mass_g", color="species",
                   barmode="overlay", opacity=0.6, nbins=30,
                   template="simple_white",
                   labels={"body_mass_g": "Body mass (g)"})
fig.show()

# %% Exercise 17.2
five = gap[gap["country"].isin(["China", "India", "Brazil",
                                "Nigeria", "Germany"])]
fig = px.line(five, x="year", y="lifeExp", color="country",
              markers=True, hover_data={"pop": ":,.0f"},
              template="simple_white",
              labels={"lifeExp": "Life expectancy", "pop": "Population",
                      "year": ""})
fig.show()

# %% Exercise 17.3
data = orders.dropna(subset=["shipping_days", "state"]).astype(
    {"shipping_days": int})
order = (data.groupby("state")["shipping_days"].mean()
         .sort_values().index.tolist())
fig = px.box(data, x="state", y="shipping_days", points="all",
             category_orders={"state": order}, template="simple_white",
             labels={"shipping_days": "Days to deliver", "state": ""})
fig.update_traces(jitter=0.4, marker_size=3)
fig.show()
print(data.groupby("state")["shipping_days"].mean().round(2)
      .sort_values().to_dict())

# %% Exercise 17.4
data = y2007.assign(log_gdp=np.log10(y2007["gdpPercap"]))
ticks = [500, 1000, 5000, 10000, 40000]
fig = px.choropleth(data, locations="iso3", color="log_gdp",
                    hover_name="country",
                    hover_data={"gdpPercap": ":$,.0f", "log_gdp": False,
                                "iso3": False},
                    color_continuous_scale="Viridis")
fig.update_coloraxes(colorbar_title="GDP per person",
                     colorbar_tickvals=np.log10(ticks),
                     colorbar_ticktext=[f"${t:,}" for t in ticks])
fig.update_geos(showframe=False, projection_type="natural earth")
fig.show()

# %% Exercise 17.5
monthly = (orders.groupby(["month", "product"])["revenue"].sum()
           .unstack(fill_value=0).cumsum().stack()
           .rename("revenue").reset_index())
monthly["month"] = monthly["month"].dt.strftime("%b")
fig = px.bar(monthly, x="revenue", y="product", orientation="h",
             animation_frame="month",
             range_x=[0, monthly["revenue"].max() * 1.05],
             template="simple_white",
             labels={"revenue": "Revenue so far ($)", "product": ""})
fig.show()

# %% Exercise 17.6
fig = px.scatter(y2007, x="gdpPercap", y="lifeExp", color="continent",
                 hover_name="country", log_x=True)
fig.write_html("chart.html")
fig.write_html("chart_cdn.html", include_plotlyjs="cdn")
fig.write_image("chart.png", scale=2)
for name in ["chart.html", "chart_cdn.html", "chart.png"]:
    print(f"{name:<15} {Path(name).stat().st_size:>10,} bytes")

# %% Exercise 17.7
by_continent = (gap.groupby(["continent", "year"], as_index=False)
                ["lifeExp"].mean())
lines = px.line(by_continent, x="year", y="lifeExp", color="continent",
                markers=True, template="simple_white")
wide = gap.pivot(index="country", columns="year", values="lifeExp")
gains = (wide[2007] - wide[1952]).nlargest(5).round(1)
table = gains.rename("years gained").to_frame().to_html()
page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Life expectancy by continent</title></head>
<body style="font-family: sans-serif; max-width: 900px; margin: auto">
<h1>Life expectancy by continent, 1952-2007</h1>
{lines.to_html(full_html=False, include_plotlyjs="cdn")}
<h2>The five biggest gains</h2>{table}</body></html>"""
Path("continents.html").write_text(page, encoding="utf-8")
print(gains)

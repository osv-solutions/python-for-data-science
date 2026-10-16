"""Chapter 17: Interactive Charts with Plotly

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch17_plotly.py

or open the notebook and run the cells in order.
"""

# %% 17.1 Charts you can explore
import pandas as pd
import plotly.express as px

gap = pd.read_csv("data/gapminder.csv")
y2007 = gap[gap["year"] == 2007]
fig = px.scatter(y2007, x="gdpPercap", y="lifeExp", size="pop",
                 color="continent", hover_name="country",
                 log_x=True, size_max=45)
fig.show()

# %% 17.1 Charts you can explore
fig = px.scatter(
    y2007, x="gdpPercap", y="lifeExp", size="pop", color="continent",
    hover_name="country", log_x=True, size_max=45,
    hover_data={"pop": ":,.0f", "gdpPercap": ":$,.0f",
                "lifeExp": ":.1f", "continent": False},
    labels={"gdpPercap": "GDP per person",
            "lifeExp": "Life expectancy", "pop": "Population",
            "continent": "Continent"},
    title="Richer countries live longer, 2007",
    template="simple_white",
)
fig.show()

# %% 17.2 Lines, bars and facets
orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].assign(
    revenue=lambda d: d["quantity"] * d["unit_price"],
    month=lambda d: d["order_date"].dt.to_period("M").dt.start_time)
monthly = (orders.groupby(["month", "product"], as_index=False)
           ["revenue"].sum())
fig = px.line(monthly, x="month", y="revenue", color="product",
              markers=True, template="simple_white",
              labels={"revenue": "Revenue ($)", "month": ""})
fig.show()

# %% 17.2 Lines, bars and facets
size_mix = (orders.groupby(["product", "bag_size"], as_index=False)
            .size())
fig = px.bar(size_mix, x="size", y="product", color="bag_size",
             orientation="h", text_auto=True, template="simple_white",
             category_orders={"bag_size": ["250g", "500g", "1kg"]},
             labels={"size": "Orders", "product": "",
                     "bag_size": "Bag size"})
fig.show()

# %% 17.3 Animation
fig = px.scatter(gap, x="gdpPercap", y="lifeExp", size="pop",
                 color="continent", hover_name="country",
                 animation_frame="year", animation_group="country",
                 log_x=True, size_max=45, range_x=[200, 60000],
                 range_y=[20, 90], template="simple_white")
fig.show()

# %% 17.4 Maps
fig = px.choropleth(y2007, locations="iso3", color="lifeExp",
                    hover_name="country",
                    color_continuous_scale="Viridis",
                    labels={"lifeExp": "Life expectancy"})
fig.update_geos(showframe=False, projection_type="natural earth")
fig.show()

# %% 17.5 Customizing a figure
products = orders.groupby("product", as_index=False)["revenue"].sum()
fig = px.bar(products.sort_values("revenue"), x="revenue",
             y="product", orientation="h", text_auto=",.0f",
             template="simple_white")
fig.update_traces(marker_color="#2a9bb0", textposition="outside",
                  cliponaxis=False)
fig.update_layout(title="Revenue by product, January to June 2026",
                  xaxis_title=None, yaxis_title=None,
                  xaxis_visible=False, height=360,
                  margin={"l": 10, "r": 60, "t": 50, "b": 10})
fig.show()

# %% 17.5 Customizing a figure
import plotly.graph_objects as go

japan = gap[gap["country"] == "Japan"]
fig = go.Figure()
fig.add_trace(go.Scatter(x=japan["year"], y=japan["lifeExp"],
                         mode="lines+markers", name="Japan"))
fig.add_hline(y=japan["lifeExp"].mean(), line_dash="dot",
              line_color="gray", line_width=1.5,
              annotation_text="1952-2007 mean")
fig.update_layout(template="simple_white", height=320,
                  yaxis_title="Life expectancy (years)")
fig.show()

# %% 17.6 Saving and sharing
from pathlib import Path

fig = px.scatter(y2007, x="gdpPercap", y="lifeExp", size="pop",
                 color="continent", hover_name="country", log_x=True)
fig.write_html("bubbles_full.html")
fig.write_html("bubbles_cdn.html", include_plotlyjs="cdn")
for name in ["bubbles_full.html", "bubbles_cdn.html"]:
    print(f"{name:<18} {Path(name).stat().st_size:>10,} bytes")

# %% 17.7 Putting it together: a one-page interactive report
bubbles = px.scatter(gap, x="gdpPercap", y="lifeExp", size="pop",
                     color="continent", hover_name="country",
                     animation_frame="year",
                     animation_group="country", log_x=True,
                     size_max=45, range_x=[200, 60000],
                     range_y=[20, 90], template="simple_white")
world = px.choropleth(y2007, locations="iso3", color="lifeExp",
                      hover_name="country",
                      color_continuous_scale="Viridis")
parts = [bubbles.to_html(full_html=False, include_plotlyjs="cdn"),
         world.to_html(full_html=False, include_plotlyjs=False)]
print(len(parts[0]) // 1000, "and", len(parts[1]) // 1000,
      "thousand characters")

# %% 17.7 Putting it together: a one-page interactive report
page = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Fifty years of world development</title></head>
<body style="font-family: sans-serif; max-width: 900px; margin: auto">
<h1>Fifty years of world development, 1952-2007</h1>
<p>Press play: almost every country moved up and to the right.</p>
{parts[0]}
<p>In 2007, the gap is mostly between Sub-Saharan Africa and the
rest of the world.</p>
{parts[1]}
</body></html>"""
Path("world_report.html").write_text(page, encoding="utf-8")
print(f"{Path('world_report.html').stat().st_size:,} bytes")

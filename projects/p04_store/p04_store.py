"""Project 4 (Intermediate): Dynamic Store Scraper

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p04_store.py

or open the notebook and run the cells in order.
"""

# %% Step 2: Scrape one day
import practice_web
import pandas as pd
from playwright.sync_api import sync_playwright

BASE = practice_web.start()
COUNT = "document.querySelectorAll('.product').length"


def load_everything(page):
    """Click "Load more" until the store shows every product."""
    button = page.locator("#load-more")
    while button.is_visible():
        before = page.locator(".product").count()
        button.click()
        page.wait_for_function(f"{COUNT} > {before}")

# %% Step 2: Scrape one day
def scrape_day(page, day):
    """Load one day's catalog and return the cards as raw text."""
    page.goto(f"{BASE}/js-store/?day={day}")
    page.wait_for_selector(".product")
    load_everything(page)
    cards = page.locator(".product")
    rows = {"id": [c.get_attribute("data-id") for c in cards.all()]}
    for field in ["name", "category", "price", "rating"]:
        rows[field] = cards.locator(f".{field}").all_text_contents()
    return pd.DataFrame(rows).assign(day=day)

# %% Step 2: Scrape one day
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    first = scrape_day(page, "2026-10-01")
    browser.close()
print(first.shape)
cols = ["id", "name", "price", "rating"]
print(first.head(3)[cols].to_string(index=False))

# %% Step 3: Two weeks of snapshots
from datetime import date, timedelta
from pathlib import Path

folder = Path("snapshots")
folder.mkdir(exist_ok=True)
days = [str(date(2026, 10, 1) + timedelta(days=n)) for n in range(14)]
todo = [d for d in days if not (folder / f"{d}.csv").exists()]
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    for day in todo:
        snapshot = scrape_day(page, day)
        snapshot.to_csv(folder / f"{day}.csv", index=False)
    browser.close()
print(len(todo), "days scraped,", len(list(folder.glob("*.csv"))),
      "snapshots")

# %% Step 4: Stack, clean and validate
raw = pd.concat([pd.read_csv(f, dtype=str)
                 for f in sorted(folder.glob("*.csv"))],
                ignore_index=True)
print(raw.shape)
parts = raw["rating"].str.extract(
    r"(?P<stars>[\d.]+) \((?P<reviews>\d+) reviews\)")
history = raw.assign(
    id=raw["id"].astype(int),
    day=pd.to_datetime(raw["day"]),
    price=pd.to_numeric(raw["price"].str.removeprefix("$")),
    stars=pd.to_numeric(parts["stars"]),
    reviews=pd.to_numeric(parts["reviews"]),
    category=raw["category"].astype("category"),
).drop(columns="rating")
print(history.dtypes)

# %% Step 4: Stack, clean and validate
per_day = history.groupby("day").size()
names_per_id = history.groupby("id")["name"].nunique()
checks = {
    "60 products every day": (per_day == 60).all(),
    "one row per product and day":
        not history.duplicated(["id", "day"]).any(),
    "no missing values": history.notna().all().all(),
    "prices positive": (history["price"] > 0).all(),
    "names stable": (names_per_id == 1).all(),
}
for name, ok in checks.items():
    print("ok  " if ok else "FAIL", name)

# %% Step 5: The price history
prices = history.pivot_table(index="name", columns="day",
                             values="price")
prices.columns = prices.columns.strftime("%m-%d")
print(prices.iloc[:4, :5])

# %% Step 5: The price history
by_id = history.groupby("id")["price"]
history["normal"] = by_id.transform("median")
history["vs_normal"] = history["price"] / history["normal"] - 1
summary = history.groupby("name").agg(
    normal=("normal", "first"), low=("price", "min"),
    high=("price", "max"))
summary["range_pct"] = (summary["high"] / summary["low"] - 1) * 100
print(summary.sort_values("range_pct", ascending=False).head(5)
      .round(2))

# %% Step 6: Sales and price drops
history["on_sale"] = history["vs_normal"] <= -0.15
sales = history[history["on_sale"]]
print(len(sales), "sale days for", sales["id"].nunique(), "products")
per_cat = history.groupby("category", observed=True)["on_sale"].mean()
print((per_cat * 100).round(1).sort_values(ascending=False).head(4))

# %% Step 6: Sales and price drops
history = history.sort_values(["id", "day"])
history["change"] = history.groupby("id")["price"].diff()
history["change_pct"] = history.groupby("id")["price"].pct_change()
today = history[history["day"] == history["day"].max()]
drops = today.nsmallest(5, "change_pct")
print(drops[["name", "price", "change", "change_pct"]].round(3)
      .to_string(index=False))

# %% Step 7: Chart the history and report the deals
import matplotlib.pyplot as plt

widest = summary.nlargest(3, "range_pct").index
fig, ax = plt.subplots(figsize=(6.4, 3.4))
for name, style in zip(widest, ["-o", "--s", ":^"]):
    ax.plot(prices.columns, prices.loc[name], style, label=name,
            markersize=4)
ax.set_xlabel("Day (October 2026)")
ax.set_ylabel("Price ($)")
ax.tick_params(axis="x", labelsize=7, rotation=45)
ax.legend(fontsize=7)
plt.show()

# %% Step 7: Chart the history and report the deals
saving = (history.groupby("name")["price"].mean()
          - history.groupby("name")["price"].min())
print(f"average price minus best price: ${saving.mean():.2f}"
      f" per product, ${saving.sum():,.2f} for the catalog")

# %% Step 7: Chart the history and report the deals
deals = (today[today["on_sale"]]
         .sort_values("vs_normal")
         [["name", "category", "price", "normal", "vs_normal"]])
deals.to_csv("deals_today.csv", index=False)
history.to_parquet("price_history.parquet", index=False)
print(f"{len(deals)} deals on {today['day'].max().date()}")
print(deals.head(5).round(2).to_string(index=False))

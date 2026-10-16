"""Solutions to the Chapter 9 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch09_solutions.py

The explanations are in ch09_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import pandas as pd
import practice_web
import requests
from playwright.sync_api import sync_playwright

BASE = practice_web.start()
COUNT = "document.querySelectorAll('.product').length"

def load_everything(page):
    button = page.locator("#load-more")
    while button.is_visible():
        before = page.locator(".product").count()
        button.click()
        page.wait_for_function(f"{COUNT} > {before}")

# %% Exercise 9.1
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/")
    page.wait_for_selector(".product")
    found = page.locator(".product .category")
    categories = found.all_text_contents()
    browser.close()
print(pd.Series(categories).value_counts())

# %% Exercise 9.2
from pathlib import Path

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/")
    page.wait_for_selector(".product")
    load_everything(page)
    page.screenshot(path="store.png", full_page=True)
    browser.close()
print(Path("store.png").stat().st_size > 0)

# %% Exercise 9.3
def scrape_store(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector(".product")
        load_everything(page)
        cards = page.locator(".product")
        rows = {"name": cards.locator(".name").all_text_contents(),
                "price": cards.locator(".price").all_text_contents()}
        browser.close()
    return pd.DataFrame(rows).assign(price=lambda d: pd.to_numeric(
        d["price"].str.removeprefix("$")))

# %% Exercise 9.3
day1 = scrape_store(f"{BASE}/js-store/?day=2026-10-01")
day2 = scrape_store(f"{BASE}/js-store/?day=2026-10-02")
both = day1.merge(day2, on="name", suffixes=("_1", "_2"))
both["change_%"] = (both["price_2"] / both["price_1"] - 1) * 100
big = both[both["change_%"].abs() > 10]
print(big.round(1).to_string(index=False))

# %% Exercise 9.4
from urllib.parse import parse_qs, urlsplit

api_pages = []
def record(response):
    if "/api/store/products" in response.url:
        query = parse_qs(urlsplit(response.url).query)
        api_pages.append(int(query["page"][0]))

# %% Exercise 9.4
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("response", record)
    page.goto(f"{BASE}/js-store/feed.html")
    while not page.locator("#end").is_visible():
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(700)
    browser.close()
print(len(api_pages), "API requests, pages", api_pages)

# %% Exercise 9.5
products, page = [], 1
while True:
    body = requests.get(f"{BASE}/api/store/products", timeout=10,
                        params={"page": page, "per_page": 12}).json()
    products += body["products"]
    if not body["has_more"]:
        break
    page += 1
paged = pd.DataFrame(products)
whole = pd.DataFrame(requests.get(f"{BASE}/api/store/products",
                                  params={"per_page": 60},
                                  timeout=10).json()["products"])
print(page, "pages,", len(paged), "products,",
      "same:", paged.equals(whole))

# %% Exercise 9.6
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/")
    page.wait_for_selector(".product")
    load_everything(page)
    cards = page.locator(".product")
    ids = [cards.nth(i).get_attribute("data-id")
           for i in range(cards.count())]
    ratings = cards.locator(".rating").all_text_contents()
    browser.close()
table = pd.DataFrame({"id": pd.to_numeric(pd.Series(ids)),
                      "rating": pd.to_numeric(
                          pd.Series(ratings).str.split().str[0])})
print(table.dtypes.astype(str).tolist())
print(table["rating"].mean().round(2))

# %% Exercise 9.7
import asyncio
import time
from playwright.async_api import async_playwright

async def store_prices(browser, day):
    page = await browser.new_page()
    await page.goto(f"{BASE}/js-store/?day={day}")
    await page.wait_for_selector(".product")
    button = page.locator("#load-more")
    while await button.is_visible():
        before = await page.locator(".product").count()
        await button.click()
        await page.wait_for_function(f"{COUNT} > {before}")
    prices = await page.locator(".price").all_text_contents()
    await page.close()
    return prices

# %% Exercise 9.7
async def compare(days):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        start = time.perf_counter()
        for day in days:
            await store_prices(browser, day)
        one_by_one = time.perf_counter() - start
        start = time.perf_counter()
        results = await asyncio.gather(
            *(store_prices(browser, day) for day in days))
        together = time.perf_counter() - start
        await browser.close()
    return one_by_one, together, [len(r) for r in results]

days = ["2026-10-01", "2026-10-02", "2026-10-03"]
seq, par, counts = asyncio.run(compare(days))
print(counts, f"one by one {seq:.1f} s, together {par:.1f} s")

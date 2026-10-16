# Solutions: Chapter 9, Scraping JavaScript Pages with Playwright

Worked solutions to the exercises at the end of Chapter 9 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch09_solutions.ipynb`](ch09_solutions.ipynb) or the script `ch09_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
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
```

</details>

## Exercise 9.1

*Open the store, watch it load, and print the categories of the first 12 products.*

With `p.chromium.launch(headless=False)`, a browser window opens and you can watch the products appear after half a second. The code below runs headless, so that it also works on a computer without a screen:

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/")
    page.wait_for_selector(".product")
    found = page.locator(".product .category")
    categories = found.all_text_contents()
    browser.close()
print(pd.Series(categories).value_counts())
```

Output:

```text
Audio        3
Computing    3
Power        2
Home         2
Wearables    2
Name: count, dtype: int64
```

The selector `.product .category` finds the category inside each card. The first 12 products are the first brand's 12 gadgets, spread over five categories.

## Exercise 9.2

*Take a full-page screenshot after all products have loaded.*

```python
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
```

Output:

```text
True
```

`full_page=True` captures the whole page, not just the visible window. Screenshots are a good record of what a page looked like when you scraped it, and help when a scraper suddenly finds nothing.

## Exercise 9.3

*Scrape two days with `scrape_store` and list the products whose price changed by more than 10%.*

```python
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
```

```python
day1 = scrape_store(f"{BASE}/js-store/?day=2026-10-01")
day2 = scrape_store(f"{BASE}/js-store/?day=2026-10-02")
both = day1.merge(day2, on="name", suffixes=("_1", "_2"))
both["change_%"] = (both["price_2"] / both["price_1"] - 1) * 100
big = both[both["change_%"].abs() > 10]
print(big.round(1).to_string(index=False))
```

Output:

```text
                          name  price_1  price_2  change_%
      Arcwell Portable SSD 1TB    105.4    131.0      24.3
Brightline Power bank 20000mAh     42.7     53.9      26.2
       Brightline Webcam 1080p     41.2     52.1      26.5
       Corvo USB-C charger 65W     43.7     35.3     -19.3
     Corvo Mechanical keyboard    121.8     98.0     -19.5
        Corvo Portable SSD 1TB    125.5    101.2     -19.3
     Dunmore Bluetooth speaker     34.2     42.3      23.4
   Dunmore Power bank 20000mAh     57.2     46.4     -19.0
       Dunmore Fitness tracker     79.2     62.6     -20.9
   Dunmore Mechanical keyboard     97.3    121.4      24.8
          Dunmore Webcam 1080p     48.5     39.2     -19.1
           Everpeak Smartwatch    230.1    283.9      23.4
```

Merging on the product name lines the two days up, with `suffixes` telling the two price columns apart. The changes larger than 10% are sales starting or ending: the store occasionally marks a product down by 20%.

## Exercise 9.4

*Record every response of the infinite-scroll page and print the API pages it asked for.*

```python
from urllib.parse import parse_qs, urlsplit

api_pages = []
def record(response):
    if "/api/store/products" in response.url:
        query = parse_qs(urlsplit(response.url).query)
        api_pages.append(int(query["page"][0]))
```

The function keeps the page number of every product API request. The page calls it for every response:

```python
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
```

Output:

```text
5 API requests, pages [1, 2, 3, 4, 5]
```

`parse_qs` splits a URL's query string into a dictionary of lists, so `query["page"][0]` is the page number as text. The page asked for five pages of 12, one per scroll, in order.

## Exercise 9.5

*Fetch the API page by page with `per_page=12`, following `has_more`.*

```python
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
```

Output:

```text
5 pages, 60 products, same: True
```

`while True` with a `break` is the natural loop when you only learn at the end of each request whether to continue. Five pages give the same 60 products as one big request, row for row.

## Exercise 9.6

*Also read each card's `data-id` and rating, as numeric columns.*

```python
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
```

Output:

```text
['int64', 'float64']
3.98
```

`cards.nth(i)` is the card at position `i`, and `get_attribute` reads its `data-id`. The rating text looks like `4.1 (1519 reviews)`, so `str.split().str[0]` keeps the first word, the number.

## Exercise 9.7

*Load three days at the same time with the asynchronous interface, and compare with one after another.*

The asynchronous interface has the same methods, used with `await`. The function below loads the store for one day in a page of a shared browser:

```python
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
```

`asyncio.gather` runs several of these at once, while a plain loop runs them one after another:

```python
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
```

Output:

```text
[60, 60, 60] one by one 7.2 s, together 2.7 s
```

All three days load all 60 products. Loading them together takes about as long as loading one, because most of the time is spent waiting for the server, and the three pages wait at the same time (*Python for All*, Chapter 21). In a notebook, which already runs an event loop, replace `asyncio.run(compare(days))` with `await compare(days)`.

"""Chapter 9: Scraping JavaScript Pages with Playwright

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch09_playwright.py

or open the notebook and run the cells in order.
"""

# %% 9.1 When requests sees an empty page
import practice_web
import requests
from bs4 import BeautifulSoup

BASE = practice_web.start()
html = requests.get(f"{BASE}/js-store/", timeout=10).text
soup = BeautifulSoup(html, "lxml")
print(len(soup.select(".product")))
print(soup.select_one("#status").get_text())
print(len(soup.select("script")), "script element(s)")

# %% 9.3 A first browser session
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/")
    page.wait_for_selector(".product")
    rendered = page.content()
    print(page.title(), "|", page.text_content("#status"))
    browser.close()
soup = BeautifulSoup(rendered, "lxml")
print(len(soup.select(".product")))

# %% 9.4 Locators and waiting
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/")
    products = page.locator(".product")
    products.first.wait_for()
    print(products.count())
    for name in products.locator(".name").all_text_contents()[:3]:
        print(name)
    print(products.first.get_attribute("data-id"))
    browser.close()

# %% 9.4 Locators and waiting
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/")
    print("right after goto:", page.locator(".product").count())
    page.wait_for_selector(".product")
    print("after waiting:   ", page.locator(".product").count())
    browser.close()

# %% 9.5 Clicking and scrolling
COUNT = "document.querySelectorAll('.product').length"

def load_everything(page):
    """Click "Load more" until the store shows every product."""
    button = page.locator("#load-more")
    while button.is_visible():
        before = page.locator(".product").count()
        button.click()
        page.wait_for_function(f"{COUNT} > {before}")

# %% 9.5 Clicking and scrolling
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/")
    page.wait_for_selector(".product")
    load_everything(page)
    print(page.text_content("#status"))
    browser.close()

# %% 9.5 Clicking and scrolling
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"{BASE}/js-store/feed.html")
    scrolls = 0
    while not page.locator("#end").is_visible():
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(700)
        scrolls += 1
    print(scrolls, "scrolls,", page.locator(".product").count(),
          "products")
    browser.close()

# %% 9.6 Finding the hidden API
seen = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("response", lambda r: seen.append((r.status, r.url)))
    page.goto(f"{BASE}/js-store/")
    page.wait_for_selector(".product")
    browser.close()
for status, url in seen:
    print(status, url.replace(BASE, ""))

# %% 9.6 Finding the hidden API
import pandas as pd

url = f"{BASE}/api/store/products"
first = requests.get(url, params={"page": 1, "per_page": 60},
                     timeout=10).json()
store = pd.DataFrame(first["products"])
print(first["total"], first["has_more"], store.shape)
print(store[["name", "category", "price", "rating"]].head(3))

# %% 9.8 Putting it together: the store, two ways
def scrape_store(url):
    """Load every product with a browser; return a clean DataFrame."""
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

# %% 9.8 Putting it together: the store, two ways
import time

start = time.perf_counter()
by_browser = scrape_store(f"{BASE}/js-store/")
t_browser = time.perf_counter() - start
start = time.perf_counter()
by_api = pd.DataFrame(requests.get(url, params={"per_page": 60},
                                   timeout=10).json()["products"])
t_api = time.perf_counter() - start
same = (by_browser["price"].values == by_api["price"].values).all()
print(len(by_browser), len(by_api), "same prices:", same)
print(f"browser {t_browser:.1f} s, API {t_api:.1f} s")

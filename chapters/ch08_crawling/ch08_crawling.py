"""Chapter 8: Scraping Many Pages

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch08_crawling.py

or open the notebook and run the cells in order.
"""

# %% 8.1 A polite session
import re
import time
import practice_web
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

BASE = practice_web.start()

# %% 8.1 A polite session
AGENT = "ds-book-crawler/1.0 (learning project; you@example.com)"

def polite_session(agent=AGENT):
    """A Session that identifies itself and retries failures."""
    session = requests.Session()
    session.headers["User-Agent"] = agent
    retry = Retry(total=3, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

session = polite_session()

# %% 8.1 A polite session
def fetch(url, session=session, delay=1.0):
    """GET a page politely: pause, retry failures, check status."""
    time.sleep(delay)
    response = session.get(url, timeout=10)
    response.raise_for_status()
    return response

# %% 8.2 Following the pager
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd

def parse_card(card, page_url):
    """Return the raw values of one book card as a dictionary."""
    link = card.select_one("h3 a")
    classes = card.select_one("p.stars")["class"]
    text = lambda css: card.select_one(css).get_text(strip=True)
    return {"title": link["title"],
            "url": urljoin(page_url, link["href"]),
            "author": text("p.author"),
            "rating": [c for c in classes if "stars-" in c][0],
            "price": text("p.price"),
            "stock": text("p.stock")}

# %% 8.2 Following the pager
def clean_books(raw):
    """Turn raw book records into a typed DataFrame."""
    books = pd.DataFrame(raw)
    return books.assign(
        author=books["author"].str.removeprefix("by "),
        rating=books["rating"].str.removeprefix("stars-").astype(int),
        price=pd.to_numeric(books["price"].str.removeprefix("$")),
        in_stock=books["stock"].eq("In stock"),
    ).drop(columns="stock")

# %% 8.2 Following the pager
def crawl_listing(start_url):
    """Follow a listing's next links; return the raw book records."""
    records, url, pages = [], start_url, 0
    while url:
        soup = BeautifulSoup(fetch(url).text, "lxml")
        cards = soup.select("article.book")
        records += [parse_card(card, url) for card in cards]
        pages += 1
        nxt = soup.select_one("ul.pager li.next a")
        url = urljoin(url, nxt["href"]) if nxt else None
    print(f"{pages} pages, {len(records)} books")
    return records

start = time.perf_counter()
first_page = f"{BASE}/shop/catalogue/page-1.html"
catalog = clean_books(crawl_listing(first_page))
print(f"{time.perf_counter() - start:.0f} seconds")

# %% 8.2 Following the pager
r = session.get(f"{BASE}/shop/catalogue/page-7.html", timeout=10)
print(r.status_code, r.raw.retries.history)

# %% 8.3 Crawling detail pages
def parse_book(html, url):
    """Return the details on one book's page."""
    soup = BeautifulSoup(html, "lxml")
    info = {row.th.get_text(strip=True): row.td.get_text(strip=True)
            for row in soup.select("#product-info tr")}
    description = soup.select_one("#description p")
    return {"url": url, "upc": info["UPC"],
            "category": info["Category"],
            "availability": info["Availability"],
            "year": int(info["Published"]),
            "description": description.get_text() if description
            else None}

# %% 8.4 Saving the raw HTML
from pathlib import Path

RAW = Path("raw_pages")
RAW.mkdir(exist_ok=True)

def get_html(url):
    """Return a page's HTML, from the raw_pages folder if saved."""
    name = url.split("://", 1)[1].replace("/", "_")
    path = RAW / name
    if not path.exists():
        path.write_text(fetch(url).text, encoding="utf-8")
    return path.read_text(encoding="utf-8")

# %% 8.4 Saving the raw HTML
poetry = catalog[catalog["url"].isin(
    clean_books(crawl_listing(
        f"{BASE}/shop/category/poetry/page-1.html"))["url"])]
start = time.perf_counter()
details = pd.DataFrame([parse_book(get_html(u), u)
                        for u in poetry["url"]])
print(len(details), f"{time.perf_counter() - start:.0f} seconds")

# %% 8.4 Saving the raw HTML
start = time.perf_counter()
details = pd.DataFrame([parse_book(get_html(u), u)
                        for u in poetry["url"]])
print(len(list(RAW.glob("*.html"))), "files,",
      f"{time.perf_counter() - start:.2f} seconds")

# %% 8.5 Combining the pages into one table
books = poetry.merge(details, on="url", validate="one_to_one")
books["copies"] = (books["availability"].str.extract(r"(\d+)")[0]
                   .astype(float).fillna(0).astype(int))
print(books[["title", "price", "copies", "year"]].head(4))
print(books["copies"].sum(), "copies;", books["description"].isna()
      .sum(), "books without a description")

# %% 8.6 Logging in: forms, sessions and cookies
login_page = BeautifulSoup(fetch(f"{BASE}/shop/login").text, "lxml")
form = login_page.select_one("form#login-form")
print(form["method"], form["action"])
for field in form.select("input"):
    print(field.get("name"), field.get("type"))

# %% 8.6 Logging in: forms, sessions and cookies
import os
from dotenv import load_dotenv

secrets = "SHOP_USER=reader\nSHOP_PASSWORD=open-sesame\n"
Path(".env").write_text(secrets, encoding="utf-8")
load_dotenv()
token = form.select_one("input[name=csrf_token]")["value"]
fields = {"csrf_token": token,
          "username": os.environ["SHOP_USER"],
          "password": os.environ["SHOP_PASSWORD"]}
action = urljoin(f"{BASE}/shop/login", form["action"])
response = session.post(action, data=fields, timeout=10)
print(response.status_code, response.url)
print(list(session.cookies.keys()))

# %% 8.6 Logging in: forms, sessions and cookies
from io import StringIO

account = fetch(f"{BASE}/shop/account").text
orders = pd.read_html(StringIO(account), attrs={"id": "orders"})[0]
print(orders)

# %% 8.7 Putting it together: a reusable crawler
class PoliteCrawler:
    """Fetch pages politely, keeping a copy of every page."""

    def __init__(self, folder, delay=1.0):
        self.folder = Path(folder)
        self.folder.mkdir(exist_ok=True)
        self.delay, self.downloads = delay, 0
        self.session = polite_session()

    def html(self, url):
        """Return a page's HTML, downloading it only once."""
        path = self.folder / (re.sub(r"\W+", "_", url) + ".html")
        if not path.exists():
            text = fetch(url, self.session, self.delay).text
            path.write_text(text, encoding="utf-8")
            self.downloads += 1
        return path.read_text(encoding="utf-8")

# %% 8.7 Putting it together: a reusable crawler
def follow(crawler, url, next_css):
    """Yield (url, soup) for a page and every page after it."""
    while url:
        soup = BeautifulSoup(crawler.html(url), "lxml")
        yield url, soup
        nxt = soup.select_one(next_css)
        url = urljoin(url, nxt["href"]) if nxt else None

# %% 8.7 Putting it together: a reusable crawler
crawler = PoliteCrawler("history_pages")
start = f"{BASE}/shop/category/history/page-1.html"
raw = [parse_card(card, url)
       for url, soup in follow(crawler, start, "li.next a")
       for card in soup.select("article.book")]
listing = clean_books(raw)
details = pd.DataFrame([parse_book(crawler.html(u), u)
                        for u in listing["url"]])
history = listing.merge(details, on="url", validate="one_to_one")
print(crawler.downloads, "pages downloaded;", history.shape)
print(history.groupby("rating")["price"].agg(["count", "mean"])
      .round(2))

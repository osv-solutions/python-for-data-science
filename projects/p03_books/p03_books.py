"""Project 3 (Beginner): Book Catalog Scraper

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p03_books.py

or open the notebook and run the cells in order.
"""

# %% Step 2: A responsible, caching crawler
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser
import pandas as pd
import practice_web
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

BASE = practice_web.start()

# %% Step 2: A responsible, caching crawler
class ResponsibleFetcher:
    """GET pages only as robots.txt allows, after the crawl delay."""

    def __init__(self, site, agent, contact):
        self.robots = RobotFileParser(f"{site}/robots.txt")
        self.robots.read()
        self.agent, self.last = agent, 0.0
        self.delay = max(self.robots.crawl_delay(agent) or 0, 1.0)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = f"{agent} ({contact})"

    def get(self, url):
        if not self.robots.can_fetch(self.agent, url):
            raise PermissionError(f"robots.txt forbids {url}")
        time.sleep(max(0, self.last + self.delay - time.monotonic()))
        self.last = time.monotonic()
        return self.session.get(url, timeout=10)

# %% Step 2: A responsible, caching crawler
RAW = Path("raw_pages")
RAW.mkdir(exist_ok=True)
fetcher = ResponsibleFetcher(BASE, "corner-books-study",
                             "you@example.com")
retry = Retry(total=3, backoff_factor=1,
              status_forcelist=[429, 500, 502, 503, 504])
fetcher.session.mount("http://", HTTPAdapter(max_retries=retry))

# %% Step 2: A responsible, caching crawler
stats = {"downloaded": 0, "from_disk": 0}

def html(url):
    """Return a page's HTML, downloading it only the first time."""
    path = RAW / (re.sub(r"\W+", "_", urlsplit(url).path) + ".html")
    if path.exists():
        stats["from_disk"] += 1
    else:
        response = fetcher.get(url)
        response.raise_for_status()
        path.write_text(response.text, encoding="utf-8")
        stats["downloaded"] += 1
    return path.read_text(encoding="utf-8")

# %% Step 3: The catalog pages
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

# %% Step 3: The catalog pages
cards, url, pages = [], f"{BASE}/shop/catalogue/page-1.html", 0
while url:
    soup = BeautifulSoup(html(url), "lxml")
    cards += [parse_card(c, url) for c in soup.select("article.book")]
    pages += 1
    nxt = soup.select_one("ul.pager li.next a")
    url = urljoin(url, nxt["href"]) if nxt else None
first = BeautifulSoup(html(f"{BASE}/shop/catalogue/page-1.html"),
                      "lxml")
claimed = int(first.select_one("p.results").get_text().split()[0])
print(pages, "pages,", len(cards), "cards; the site says", claimed)

# %% Step 4: The book pages
def parse_book(page, url):
    """Return the details on one book's page."""
    soup = BeautifulSoup(page, "lxml")
    info = {row.th.get_text(strip=True): row.td.get_text(strip=True)
            for row in soup.select("#product-info tr")}
    description = soup.select_one("#description p")
    return {"url": url, "upc": info["UPC"],
            "category": info["Category"],
            "availability": info["Availability"],
            "year": int(info["Published"]),
            "description": description.get_text() if description
            else None}

# %% Step 4: The book pages
details = []
for n, card in enumerate(cards, start=1):
    details.append(parse_book(html(card["url"]), card["url"]))
    if n % 100 == 0:
        print(n, "book pages", stats)

# %% Step 5: Merge and clean
books = pd.merge(pd.DataFrame(cards), pd.DataFrame(details),
                 on="url", validate="one_to_one")
books = books.assign(
    author=books["author"].str.removeprefix("by "),
    rating=books["rating"].str.removeprefix("stars-").astype(int),
    price=pd.to_numeric(books["price"].str.removeprefix("$")),
    in_stock=books["stock"].eq("In stock"),
    copies=books["availability"].str.extract(r"(\d+)")[0]
    .astype(float).fillna(0).astype(int),
    category=books["category"].astype("category"),
).drop(columns=["stock", "availability"])
print(books.shape)
print(books.dtypes.value_counts())

# %% Step 6: Validate the dataset
side = BeautifulSoup(html(f"{BASE}/shop/"), "lxml")
site_counts = {li.a.get_text(): int(li.get_text().split("(")[-1]
                                    .rstrip(")"))
               for li in side.select("ul.categories li")}
print(site_counts["Mystery"], len(site_counts))

# %% Step 6: Validate the dataset
checks = {
    "300 books": len(books) == claimed,
    "unique URLs": books["url"].is_unique,
    "unique UPCs": books["upc"].is_unique,
    "category counts match the site": (
        books["category"].value_counts().to_dict() == site_counts),
    "in_stock agrees with copies": (
        books["in_stock"] == (books["copies"] > 0)).all(),
    "prices are positive": (books["price"] > 0).all(),
}
for name, ok in checks.items():
    print(f"{'ok  ' if ok else 'FAIL'} {name}")

# %% Step 6: Validate the dataset
print(books.isna().sum()[books.isna().sum() > 0])
print(books["year"].agg(["min", "max"]).tolist())

# %% Step 7: What the catalog says
summary = books.groupby("category", observed=True).agg(
    books=("title", "size"),
    median_price=("price", "median"),
    out_of_stock=("in_stock", lambda s: round((~s).mean() * 100)),
    copies=("copies", "sum"))
print(summary.sort_values("median_price", ascending=False))

# %% Step 7: What the catalog says
by_rating = books.groupby("rating")["price"].agg(["count", "median"])
print(by_rating.round(2))
print("correlation:", books["rating"].corr(books["price"]).round(2))

# %% Step 8: Save the dataset and its documentation
import json
from datetime import date

# %% Step 8: Save the dataset and its documentation
dictionary = {
    "source": f"{BASE}/shop/ (catalog and book pages)",
    "collected": date(2026, 10, 15).isoformat(),
    "columns": {
        "title": "full title, from the link's title attribute",
        "url": "the book's page", "author": "author's name",
        "rating": "stars, 1 to 5", "price": "US dollars",
        "in_stock": "listing page says In stock",
        "upc": "product code", "category": "one of ten categories",
        "year": "year of publication", "copies": "copies in stock",
        "description": "book page text; missing for some books"}}
Path("books.json").write_text(json.dumps(dictionary, indent=2))

# %% Step 8: Save the dataset and its documentation
books.to_csv("books.csv", index=False)
books.to_parquet("books.parquet", index=False)
print(sorted(p.name for p in Path(".").glob("books.*")))

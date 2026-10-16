"""Solutions to the Chapter 8 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch08_solutions.py

The explanations are in ch08_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import re
import time
from pathlib import Path
from urllib.parse import urljoin
import pandas as pd
import practice_web
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

BASE = practice_web.start()

def polite_session():
    session = requests.Session()
    session.headers["User-Agent"] = "ds-book-crawler/1.0"
    retry = Retry(total=3, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session

session = polite_session()

def fetch(url, session=session, delay=1.0):
    time.sleep(delay)
    response = session.get(url, timeout=10)
    response.raise_for_status()
    return response

def parse_card(card, page_url):
    link = card.select_one("h3 a")
    classes = card.select_one("p.stars")["class"]
    text = lambda css: card.select_one(css).get_text(strip=True)
    return {"title": link["title"],
            "url": urljoin(page_url, link["href"]),
            "author": text("p.author"),
            "rating": [c for c in classes if "stars-" in c][0],
            "price": text("p.price"), "stock": text("p.stock")}

def clean_books(raw):
    books = pd.DataFrame(raw)
    return books.assign(
        author=books["author"].str.removeprefix("by "),
        rating=books["rating"].str.removeprefix("stars-").astype(int),
        price=pd.to_numeric(books["price"].str.removeprefix("$")),
        in_stock=books["stock"].eq("In stock"),
    ).drop(columns="stock")

def parse_book(html, url):
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

class PoliteCrawler:
    def __init__(self, folder, delay=1.0):
        self.folder = Path(folder)
        self.folder.mkdir(exist_ok=True)
        self.delay, self.downloads = delay, 0
        self.session = polite_session()

    def html(self, url):
        path = self.folder / (re.sub(r"\W+", "_", url) + ".html")
        if not path.exists():
            text = fetch(url, self.session, self.delay).text
            path.write_text(text, encoding="utf-8")
            self.downloads += 1
        return path.read_text(encoding="utf-8")

def follow(crawler, url, next_css):
    while url:
        soup = BeautifulSoup(crawler.html(url), "lxml")
        yield url, soup
        nxt = soup.select_one(next_css)
        url = urljoin(url, nxt["href"]) if nxt else None

# %% Exercise 8.1
def crawl_listing(start_url, max_pages=None):
    """Follow next links; return raw book records."""
    records, url, pages = [], start_url, 0
    while url and (max_pages is None or pages < max_pages):
        soup = BeautifulSoup(fetch(url).text, "lxml")
        cards = soup.select("article.book")
        records += [parse_card(card, url) for card in cards]
        pages += 1
        nxt = soup.select_one("ul.pager li.next a")
        url = urljoin(url, nxt["href"]) if nxt else None
    return records

travel = clean_books(crawl_listing(
    f"{BASE}/shop/category/travel/page-1.html"))
print(len(travel), "books,", (~travel["in_stock"]).sum(),
      "out of stock")

# %% Exercise 8.2
three = crawl_listing(f"{BASE}/shop/catalogue/page-1.html",
                      max_pages=3)
print(len(three))

# %% Exercise 8.3
crawler = PoliteCrawler("poetry_pages")
start = f"{BASE}/shop/category/poetry/page-1.html"
urls = [parse_card(c, u)["url"]
        for u, soup in follow(crawler, start, "li.next a")
        for c in soup.select("article.book")]
for url in urls:
    crawler.html(url)
print(crawler.downloads, "pages saved")

# %% Exercise 8.3
rows = []
for path in Path("poetry_pages").glob("*_shop_book_*.html"):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    details = parse_book(str(soup), str(path))
    rows.append({"title": soup.h1.get_text(),
                 "year": details["year"]})
years = pd.DataFrame(rows).sort_values("year")
print(years.iloc[[0, -1]].to_string(index=False))

# %% Exercise 8.4
bare = requests.Session()          # no retry policy at all
records, failed = [], []
for n in range(1, 16):
    url = f"{BASE}/shop/catalogue/page-{n}.html"
    try:
        soup = BeautifulSoup(fetch(url, bare, delay=0.2).text, "lxml")
    except requests.HTTPError as err:
        failed.append((n, err.response.status_code))
        continue
    cards = soup.select("article.book")
    records += [parse_card(card, url) for card in cards]
print(len(records), "books; failed pages:", failed)

# %% Exercise 8.5
s = requests.Session()
form = BeautifulSoup(s.get(f"{BASE}/shop/login").text, "lxml")
token = form.select_one("input[name=csrf_token]")["value"]
bad = s.post(f"{BASE}/shop/login", timeout=10,
             data={"csrf_token": token, "username": "reader",
                   "password": "wrong"})
page = BeautifulSoup(bad.text, "lxml")
print(bad.status_code, page.select_one("p.error").get_text())

# %% Exercise 8.5
token = page.select_one("input[name=csrf_token]")["value"]
s.post(f"{BASE}/shop/login", timeout=10,
       data={"csrf_token": token, "username": "reader",
             "password": "open-sesame"})
print(s.get(f"{BASE}/shop/account").url)
s.get(f"{BASE}/shop/logout")
print(s.get(f"{BASE}/shop/account").url)

# %% Exercise 8.6
def category_books(crawler, slug):
    start = f"{BASE}/shop/category/{slug}/page-1.html"
    raw = [parse_card(c, u)
           for u, soup in follow(crawler, start, "li.next a")
           for c in soup.select("article.book")]
    listing = clean_books(raw)
    details = pd.DataFrame([parse_book(crawler.html(u), u)
                            for u in listing["url"]])
    return listing.merge(details, on="url", validate="one_to_one")

crawler = PoliteCrawler("two_categories")
both = pd.concat([category_books(crawler, s)
                  for s in ["mystery", "romance"]], ignore_index=True)
both["copies"] = (both["availability"].str.extract(r"(\d+)")[0]
                  .astype(float).fillna(0))
print((both["copies"] < 5).groupby(both["category"]).mean().round(2))

# %% Exercise 8.7
def crawl_details(self, urls, parse):
    """Parse every page that can be fetched; report what happened."""
    before, records, failed = self.downloads, [], []
    for url in urls:
        try:
            records.append(parse(self.html(url), url))
        except requests.HTTPError:
            failed.append(url)
    new = self.downloads - before
    print(f"{new} downloaded, {len(urls) - new - len(failed)} from "
          f"disk, {len(failed)} failed")
    return records

PoliteCrawler.crawl_details = crawl_details

# %% Exercise 8.7
urls = list(both["url"][:3]) + [f"{BASE}/shop/book/no-such-book.html"]
records = crawler.crawl_details(urls, parse_book)
print(len(records))

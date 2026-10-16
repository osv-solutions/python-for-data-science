# Solutions: Chapter 8, Scraping Many Pages

Worked solutions to the exercises at the end of Chapter 8 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch08_solutions.ipynb`](ch08_solutions.ipynb) or the script `ch08_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
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
```

</details>

## Exercise 8.1

*Crawl the Travel category and print how many books it has and how many are out of stock.*

```python
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
```

Output:

```text
30 books, 2 out of stock
```

This version of `crawl_listing` already has the `max_pages` argument of exercise 8.2. The Travel category has 30 books on two pages, two of them sold out.

## Exercise 8.2

*Stop after a maximum number of pages, and test with 3 pages of the full catalog.*

```python
three = crawl_listing(f"{BASE}/shop/catalogue/page-1.html",
                      max_pages=3)
print(len(three))
```

Output:

```text
60
```

The loop condition stops as soon as `pages` reaches `max_pages`; `None`, the default, means no limit. Three pages hold 60 books. A page limit is useful while developing a crawler and as a safety net against a pager that never ends.

## Exercise 8.3

*Reparse the poetry books from the saved pages, without network access, and find the oldest and newest book.*

The chapter saved the pages in its own working folder. This solution first saves them in a folder of its own, with the `PoliteCrawler`, and then parses from disk only:

```python
crawler = PoliteCrawler("poetry_pages")
start = f"{BASE}/shop/category/poetry/page-1.html"
urls = [parse_card(c, u)["url"]
        for u, soup in follow(crawler, start, "li.next a")
        for c in soup.select("article.book")]
for url in urls:
    crawler.html(url)
print(crawler.downloads, "pages saved")
```

Output:

```text
30 pages saved
```

Now the reparse uses nothing but the files. Each saved book page contains its own title in the `h1`:

```python
rows = []
for path in Path("poetry_pages").glob("*_shop_book_*.html"):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    details = parse_book(str(soup), str(path))
    rows.append({"title": soup.h1.get_text(),
                 "year": details["year"]})
years = pd.DataFrame(rows).sort_values("year")
print(years.iloc[[0, -1]].to_string(index=False))
```

Output:

```text
                           title  year
        Hidden Machines: A Novel  1959
The Island of the Golden Orchard  2024
```

The crawler saved 30 pages: the category's two listing pages and its 28 book pages. `glob("*_shop_book_*.html")` picks only the book pages among the saved files, because the file names come from the URLs. `iloc[[0, -1]]` takes the first and last rows of the sorted table: the oldest and the newest book.

## Exercise 8.4

*Turn off retries and crawl the full catalog: what happens at page 7? Log and skip failing pages.*

Without a retry policy, the first request for page 7 fails with a 503 and `raise_for_status` raises an `HTTPError`, which stops the crawl. A more robust loop catches the error, records the page, and still follows the pager. The next link can't be read from a page that failed, so the loop also needs a fallback; here it builds the next page's URL from the page number:

```python
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
```

Output:

```text
280 books; failed pages: [(7, 503)]
```

The practice server fails page 7 the first time it is asked for after it starts, and in this run it does: 280 books are collected and `failed` is `[(7, 503)]`. One page was skipped and logged, everything else was collected, and the list says which page to try again later. The short delay of 0.2 seconds keeps the exercise quick; use the site's crawl delay in real work.

## Exercise 8.5

*Log in with a wrong password, then log out and show that the account page redirects to the login page.*

```python
s = requests.Session()
form = BeautifulSoup(s.get(f"{BASE}/shop/login").text, "lxml")
token = form.select_one("input[name=csrf_token]")["value"]
bad = s.post(f"{BASE}/shop/login", timeout=10,
             data={"csrf_token": token, "username": "reader",
                   "password": "wrong"})
page = BeautifulSoup(bad.text, "lxml")
print(bad.status_code, page.select_one("p.error").get_text())
```

Output:

```text
200 Wrong user name or password.
```

The server answers 200, not an error code, and shows the login form again with a message. That is common: a scraper must look at the page, not just the status, to know whether a login worked. Now a successful login, a logout, and the account page:

```python
token = page.select_one("input[name=csrf_token]")["value"]
s.post(f"{BASE}/shop/login", timeout=10,
       data={"csrf_token": token, "username": "reader",
             "password": "open-sesame"})
print(s.get(f"{BASE}/shop/account").url)
s.get(f"{BASE}/shop/logout")
print(s.get(f"{BASE}/shop/account").url)
```

Output:

```text
http://127.0.0.1:8020/shop/account
http://127.0.0.1:8020/shop/login?next=/shop/account
```

After the login, the account page loads at its own URL; after the logout, the same request is redirected to `/shop/login?next=/shop/account`, because the session ID is no longer valid.

## Exercise 8.6

*Collect two categories with the crawler and compare the share of books with fewer than five copies.*

```python
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
```

Output:

```text
category
Mystery    0.41
Romance    0.48
Name: copies, dtype: float64
```

`category_books` packages the chapter's steps for any category. Grouping the Boolean "fewer than five copies" by category and taking the mean gives each category's share of low-stock books. (Sold-out books, with 0 copies, count as low stock here.)

## Exercise 8.7

*Add a `crawl_details(urls, parse)` method that skips failing pages and prints a summary.*

```python
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
```

The method counts how many pages it actually downloaded by comparing `downloads` before and after; the pages that neither failed nor were downloaded came from disk. A test with one URL that doesn't exist:

```python
urls = list(both["url"][:3]) + [f"{BASE}/shop/book/no-such-book.html"]
records = crawler.crawl_details(urls, parse_book)
print(len(records))
```

Output:

```text
0 downloaded, 3 from disk, 1 failed
3
```

The three real books come from the folder saved in exercise 8.6, and the made-up URL fails with a 404, which the retry policy doesn't retry. Three records are returned.

"""Solutions to the Chapter 7 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch07_solutions.py

The explanations are in ch07_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
from io import StringIO
from urllib.parse import urljoin
import pandas as pd
import practice_web
import requests
from bs4 import BeautifulSoup

BASE = practice_web.start()

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

def scrape_listing(url):
    soup = BeautifulSoup(requests.get(url, timeout=10).text, "lxml")
    return [parse_card(c, url) for c in soup.select("article.book")]

# %% Exercise 7.1
page_url = f"{BASE}/shop/catalogue/page-1.html"
soup = BeautifulSoup(requests.get(page_url, timeout=10).text, "lxml")
for card in soup.select("article.book"):
    if card.select_one("p.stock.out-of-stock"):
        print(card.select_one("h3 a")["title"], "|",
              card.select_one("p.price").get_text())

# %% Exercise 7.2
for link in soup.select("ul.pager a"):
    print(link.get_text(), "->", urljoin(page_url, link["href"]))

# %% Exercise 7.3
frames = []
for category in ["mystery", "travel", "cooking"]:
    url = f"{BASE}/shop/category/{category}/page-1.html"
    frames.append(clean_books(scrape_listing(url))
                  .assign(category=category))
three = pd.concat(frames, ignore_index=True)
print(three.groupby("category")[["price", "rating"]].mean().round(2))

# %% Exercise 7.4
book_url = clean_books(scrape_listing(page_url))["url"].iloc[0]
book = BeautifulSoup(requests.get(book_url, timeout=10).text, "lxml")
info = {row.th.get_text(strip=True): row.td.get_text(strip=True)
        for row in book.select("#product-info tr")}
for label, value in info.items():
    print(f"{label:<13}{value}")

# %% Exercise 7.5
table = pd.read_html(StringIO(str(book)),
                     attrs={"id": "product-info"})[0]
print(table)
print(table.dtypes.astype(str).tolist())

# %% Exercise 7.6
page = requests.get(f"{BASE}/data/life-expectancy-2007.html",
                    timeout=10).text
tables = pd.read_html(StringIO(page), thousands=",")
page_soup = BeautifulSoup(page, "lxml")
heads = [h.get_text() for h in page_soup.select("h2")]
world = pd.concat([t.assign(continent=c)
                   for c, t in zip(heads, tables)], ignore_index=True)
top3 = (world.sort_values("Population", ascending=False)
        .groupby("continent").head(3))
print(top3[["continent", "Country", "Population"]]
      .sort_values(["continent", "Population"],
                   ascending=[True, False]).to_string(index=False))

# %% Exercise 7.7
def text_or_none(card, css):
    element = card.select_one(css)
    return element.get_text(strip=True) if element else None

def parse_card_safe(card, page_url):
    link = card.select_one("h3 a")
    stars = card.select_one("p.stars")
    rating = None
    if stars:
        classes = stars["class"]
        rating = next((c for c in classes if "stars-" in c), None)
    return {"title": link["title"],
            "url": urljoin(page_url, link["href"]),
            "rating": rating, "price": text_or_none(card, "p.price")}

# %% Exercise 7.7
card = soup.select_one("article.book")
card.select_one("p.price").decompose()
print(parse_card_safe(card, page_url)["price"])
print(parse_card_safe(card, page_url)["rating"])

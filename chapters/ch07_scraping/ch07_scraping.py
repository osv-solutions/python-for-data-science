"""Chapter 7: Web Scraping with requests and Beautiful Soup

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch07_scraping.py

or open the notebook and run the cells in order.
"""

# %% 7.1 From page to table
import practice_web
import requests
from bs4 import BeautifulSoup

BASE = practice_web.start()
response = requests.get(f"{BASE}/shop/", timeout=10)
soup = BeautifulSoup(response.text, "lxml")
print(response.status_code, soup.title.get_text())

# %% 7.2 Beautiful Soup in five minutes
html_doc = """<html><head><title>Tiny Shop</title></head><body>
<h1>New this week</h1>
<ul id="new">
  <li class="book"><a href="/shop/book/emma-1.html">Emma</a>
    <span class="price">$9.99</span></li>
  <li class="book sale"><a href="/shop/book/dune-2.html">Dune</a>
    <span class="price">$12.50</span></li>
</ul></body></html>"""
mini = BeautifulSoup(html_doc, "lxml")
print(mini.title.get_text(), "|", mini.h1.get_text())

# %% 7.2 Beautiful Soup in five minutes
first = mini.find("li", class_="book")
print(first.a.get_text(), first.a["href"], first.get("id"))
for li in mini.find_all("li", class_="book"):
    price = li.find("span", class_="price").get_text()
    print(li.a.get_text(), price, li["class"])

# %% 7.2 Beautiful Soup in five minutes
print([a.get_text() for a in mini.select("ul#new li.book a")])
print(mini.select_one("li.sale span.price").get_text())
print(first.parent.name, first.find_next_sibling("li").a.get_text())

# %% 7.3 Looking at a page like a scraper
card = soup.select_one("article.book")
print(card.prettify()[:620])

# %% 7.4 CSS selectors in depth
print(len(soup.select("article.book")))
print(len(soup.select("p.stock.out-of-stock")))
print(soup.select_one("ul.pager > li.current").get_text())
print([a.get_text() for a in soup.select("ul.categories a")][:4])

# %% 7.5 Text, attributes and links
link = card.select_one("h3 a")
print(link["href"])
print(card.select_one("p.stars")["class"])
for a in soup.select("article.book h3 a")[1:4]:
    print(a.get_text(strip=True), "|", a["title"])

# %% 7.5 Text, attributes and links
from pprint import pprint
from urllib.parse import urljoin

page_url = f"{BASE}/shop/catalogue/page-1.html"
print(urljoin(page_url, link["href"]))
print(urljoin(page_url, "page-2.html"))

# %% 7.5 Text, attributes and links
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

raw = [parse_card(c, page_url) for c in soup.select("article.book")]
pprint(raw[0], width=68)

# %% 7.6 Cleaning scraped values
import pandas as pd

books = pd.DataFrame(raw)
print(books.dtypes.value_counts())
print(books[["rating", "price", "stock"]].head(3))

# %% 7.6 Cleaning scraped values
clean = books.assign(
    author=books["author"].str.removeprefix("by "),
    rating=books["rating"].str.removeprefix("stars-").astype(int),
    price=pd.to_numeric(books["price"].str.removeprefix("$")),
    in_stock=books["stock"].eq("In stock"),
).drop(columns="stock")
print(clean.dtypes)

# %% 7.6 Cleaning scraped values
print(clean[["title", "rating", "price", "in_stock"]].head(3))
print(clean.groupby("rating")["price"].mean().round(2))

# %% 7.7 Tables with read_html
from io import StringIO

page = requests.get(f"{BASE}/data/life-expectancy-2007.html",
                    timeout=10).text
tables = pd.read_html(StringIO(page), thousands=",")
print(len(tables))
print(tables[0].head(3))
print(tables[0].dtypes)

# %% 7.7 Tables with read_html
page_soup = BeautifulSoup(page, "lxml")
continents = [h2.get_text() for h2 in page_soup.select("h2")]
world = pd.concat(
    [t.assign(continent=c) for c, t in zip(continents, tables)],
    ignore_index=True)
world["GDP per person"] = pd.to_numeric(
    world["GDP per person"].str.replace("[$,]", "", regex=True))
print(world.shape)
print(world.groupby("continent")["Life expectancy"].median())

# %% 7.8 When read_html isn't enough: tables by hand
page = requests.get(f"{BASE}/data/largest-cities.html",
                    timeout=10).text
cities = pd.read_html(StringIO(page))[0]
for column in cities.columns:
    print(column)
print(cities.head(3))

# %% 7.8 When read_html isn't enough: tables by hand
table = BeautifulSoup(page, "lxml").select_one("table.data")
rows, country = [], None
for tr in table.select("tbody tr"):
    cells = tr.find_all("td")
    if cells[0].has_attr("rowspan"):      # a new country starts
        country = cells[0].get_text(strip=True)
        cells = cells[1:]
    link = cells[0].find("a")
    note = cells[1].find("sup")
    rows.append({"country": country, "city": link.get_text(),
                 "url": urljoin(BASE, link["href"]),
                 "note": note.get_text(strip=True) if note else "",
                 "proper": cells[1].contents[0],
                 "metro": cells[2].text})

# %% 7.8 When read_html isn't enough: tables by hand
big = pd.DataFrame(rows)
for col in ["proper", "metro"]:
    big[col] = pd.to_numeric(big[col].str.replace(",", ""))
big["metro_x"] = (big["metro"] / big["proper"]).round(1)
print(big[["country", "city", "note", "metro_x"]].head(4))
print(big.loc[0, "url"])

# %% 7.9 Putting it together: a catalog page to a clean table
def scrape_listing(url, session=requests):
    """Return the raw book records on one catalog or category page."""
    response = session.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    return [parse_card(c, url) for c in soup.select("article.book")]

def clean_books(raw):
    """Turn raw book records into a typed DataFrame."""
    books = pd.DataFrame(raw)
    return books.assign(
        author=books["author"].str.removeprefix("by "),
        rating=books["rating"].str.removeprefix("stars-").astype(int),
        price=pd.to_numeric(books["price"].str.removeprefix("$")),
        in_stock=books["stock"].eq("In stock"),
    ).drop(columns="stock")

# %% 7.9 Putting it together: a catalog page to a clean table
url = f"{BASE}/shop/category/poetry/page-1.html"
poetry = clean_books(scrape_listing(url))
print(len(poetry), poetry["price"].mean().round(2))
cols = ["title", "rating", "price"]
print(poetry.nlargest(3, "rating")[cols].to_string(index=False))

# Solutions: Chapter 7, Web Scraping with requests and Beautiful Soup

Worked solutions to the exercises at the end of Chapter 7 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch07_solutions.ipynb`](ch07_solutions.ipynb) or the script `ch07_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
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
```

</details>

## Exercise 7.1

*From the first catalog page, print the titles and prices of the books that are out of stock.*

```python
page_url = f"{BASE}/shop/catalogue/page-1.html"
soup = BeautifulSoup(requests.get(page_url, timeout=10).text, "lxml")
for card in soup.select("article.book"):
    if card.select_one("p.stock.out-of-stock"):
        print(card.select_one("h3 a")["title"], "|",
              card.select_one("p.price").get_text())
```

Output:

```text
The Lantern of the Hidden Kitchen | $37.45
The Forgotten Bridge | $33.59
The Compass of the Distant Harbor | $38.77
```

The selector `p.stock.out-of-stock` matches only stock paragraphs with both classes, so `select_one` returns an element for sold-out books and `None` for the others. The three sold-out books on the page are listed with their full titles from the `title` attribute.

## Exercise 7.2

*Write one selector for the pager's links and print the next page as an absolute URL.*

```python
for link in soup.select("ul.pager a"):
    print(link.get_text(), "->", urljoin(page_url, link["href"]))
```

Output:

```text
next -> http://127.0.0.1:8020/shop/catalogue/page-2.html
```

`ul.pager a` matches every link inside the pager. On page 1 there is only a "next" link; on later pages there is also a "previous" one. `urljoin` resolves the relative `page-2.html` against the current page's URL.

## Exercise 7.3

*Scrape the first page of three categories and compare their average prices and ratings.*

```python
frames = []
for category in ["mystery", "travel", "cooking"]:
    url = f"{BASE}/shop/category/{category}/page-1.html"
    frames.append(clean_books(scrape_listing(url))
                  .assign(category=category))
three = pd.concat(frames, ignore_index=True)
print(three.groupby("category")[["price", "rating"]].mean().round(2))
```

Output:

```text
          price  rating
category               
cooking   29.47     4.0
mystery   22.33     3.5
travel    37.68     3.7
```

Each category page is scraped and cleaned with the chapter's functions, given a `category` column, and the three tables are stacked with `pd.concat` (Chapter 13). Only the first page of each category is included, at most 20 books each, which is enough for a first comparison.

## Exercise 7.4

*Extract the values of a book page's `#product-info` table into a dictionary.*

```python
book_url = clean_books(scrape_listing(page_url))["url"].iloc[0]
book = BeautifulSoup(requests.get(book_url, timeout=10).text, "lxml")
info = {row.th.get_text(strip=True): row.td.get_text(strip=True)
        for row in book.select("#product-info tr")}
for label, value in info.items():
    print(f"{label:<13}{value}")
```

Output:

```text
UPC          099936f675cc
Category     Children
Price        $11.97
Availability In stock (22 available)
Published    2022
```

Each table row has one `th` (the label) and one `td` (the value). `row.th` is a shortcut for the first `th` inside the row.

## Exercise 7.5

*Use `read_html` on the same book page and compare.*

```python
table = pd.read_html(StringIO(str(book)),
                     attrs={"id": "product-info"})[0]
print(table)
print(table.dtypes.astype(str).tolist())
```

Output:

```text
              0                        1
0           UPC             099936f675cc
1      Category                 Children
2         Price                   $11.97
3  Availability  In stock (22 available)
4     Published                     2022
['str', 'str']
```

`read_html` finds the same five rows, with the labels in column 0 and the values in column 1. It gets the structure right with no code at all, but every value is text in one column: the price keeps its dollar sign, the availability is a sentence, and the year can't be a number in a column that also holds text. For a two-column "label: value" table like this, the dictionary from exercise 7.4 is easier to clean.

## Exercise 7.6

*Find the three most populous countries on each continent.*

```python
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
```

Output:

```text
continent       Country  Population
   Africa       Nigeria   135031164
   Africa         Egypt    80264543
   Africa      Ethiopia    76511887
 Americas United States   301139947
 Americas        Brazil   190010647
 Americas        Mexico   108700891
     Asia         China  1318683096
     Asia         India  1110396331
     Asia     Indonesia   223547000
   Europe       Germany    82400996
   Europe        Turkey    71158647
   Europe        France    61083916
  Oceania     Australia    20434176
  Oceania   New Zealand     4115771
```

Sorting the whole table by population and then taking `groupby(...).head(3)` keeps the first three rows of each continent, which are its three largest. Oceania has only two countries in the data, so it contributes two rows.

## Exercise 7.7

*Make `parse_card` work when a card has no rating or no price.*

```python
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
```

Every lookup that might find nothing is checked before it is used. `next(generator, None)` returns `None` instead of raising an error when no class matches. To test it, remove the price from a card with `decompose`, which deletes an element from the tree:

```python
card = soup.select_one("article.book")
card.select_one("p.price").decompose()
print(parse_card_safe(card, page_url)["price"])
print(parse_card_safe(card, page_url)["rating"])
```

Output:

```text
None
stars-4
```

The price is now `None`, and the rest of the record is unaffected. In the cleaning step, `pd.to_numeric` turns `None` into `NaN`, which pandas treats as missing.

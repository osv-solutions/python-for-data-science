# Solutions: Chapter 10, Scraping Responsibly

Worked solutions to the exercises at the end of Chapter 10 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch10_solutions.ipynb`](ch10_solutions.ipynb) or the script `ch10_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import practice_web
import requests
from bs4 import BeautifulSoup

BASE = practice_web.start()
robots = RobotFileParser(f"{BASE}/robots.txt")
robots.read()

class ResponsibleFetcher:
    def __init__(self, site, agent, contact):
        self.robots = RobotFileParser(f"{site}/robots.txt")
        self.robots.read()
        self.agent = agent
        self.delay = max(self.robots.crawl_delay(agent) or 0, 1.0)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = f"{agent} ({contact})"
        self.log, self.last = [], 0.0

    def get(self, url):
        if not self.robots.can_fetch(self.agent, url):
            raise PermissionError(f"robots.txt forbids {url}")
        wait = self.last + self.delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.last = time.monotonic()
        response = self.session.get(url, timeout=10)
        self.log.append((self.last, urlsplit(url).path,
                         response.status_code))
        return response
```

</details>

## Exercise 10.1

*Check whether GreedyBot and your crawler may fetch `/robots.txt` and `/shop/terms.html`.*

```python
for agent in ["GreedyBot", "ds-book-crawler"]:
    for path in ["/robots.txt", "/shop/terms.html"]:
        print(f"{agent:<16}{path:<18}"
              f"{robots.can_fetch(agent, BASE + path)}")
```

Output:

```text
GreedyBot       /robots.txt       True
GreedyBot       /shop/terms.html  False
ds-book-crawler /robots.txt       True
ds-book-crawler /shop/terms.html  True
```

`robotparser` always allows `/robots.txt` itself, since every crawler must read it to learn the rules; beyond that, GreedyBot is shut out of everything by `Disallow: /`, including the terms page. Our crawler may fetch both.

## Exercise 10.2

*Count the book pages in the sitemap.*

```python
sitemap = requests.get(f"{BASE}/sitemap.xml", timeout=10).text
locs = [loc.get_text() for loc in
        BeautifulSoup(sitemap, "xml").select("loc")]
books = [u for u in locs if "/shop/book/" in u]
print(len(locs), "URLs,", len(books), "book pages")
```

Output:

```text
315 URLs, 300 book pages
```

The `"xml"` parser (provided by `lxml`) reads XML documents such as sitemaps, keeping tag names exactly as written. The sitemap lists the 15 catalog pages and the 300 book pages: a crawler could get every book's URL from it with one request instead of crawling the catalog.

## Exercise 10.3

*Write `polite_delay(robots, agent, minimum=1.0)` and test it with a parsed robots file.*

```python
def polite_delay(robots, agent, minimum=1.0):
    """The site's crawl delay, but never less than minimum."""
    return max(robots.crawl_delay(agent) or 0, minimum)

slow = RobotFileParser()
slow.parse(["User-agent: *", "Crawl-delay: 5", "Disallow: /private/"])
print(polite_delay(slow, "anybot"), polite_delay(robots, "anybot"))
print(polite_delay(RobotFileParser(), "anybot"))
```

Output:

```text
5 1
1.0
```

`parse` reads rules from a list of lines instead of a URL, which makes testing easy. The site that asks for 5 seconds gets 5, Corner Books gets its 1, and a parser with no rules, whose `crawl_delay` returns `None`, gets the minimum.

## Exercise 10.4

*Add a `summary()` method to `ResponsibleFetcher`.*

```python
from collections import Counter

def summary(self):
    times = [t for t, _, _ in self.log]
    gaps = [b - a for a, b in zip(times, times[1:])]
    return {"requests": len(self.log),
            "statuses": dict(Counter(s for _, _, s in self.log)),
            "average gap": round(sum(gaps) / len(gaps), 2) if gaps
            else None,
            "total time": round(times[-1] - times[0], 2) if times
            else 0}
```

The method is attached to the class, as in the chapter, and tried on four requests:

```python
ResponsibleFetcher.summary = summary
fetcher = ResponsibleFetcher(BASE, "ds-book-crawler",
                             "you@example.com")
for n in (1, 2, 3, 99):
    fetcher.get(f"{BASE}/shop/catalogue/page-{n}.html")
for key, value in fetcher.summary().items():
    print(f"{key:<12}{value}")
```

Output:

```text
requests    4
statuses    {200: 3, 404: 1}
average gap 1.0
total time  3.0
```

`Counter` counts the status codes. The fourth request asks for a page that doesn't exist, so the summary shows three 200s and one 404, with the requests one second apart.

## Exercise 10.5

*Write a source record for Corner Books and save it to JSON.*

```python
import json
from pathlib import Path

record = {
    "source": "Corner Books (practice site)",
    "url": f"{BASE}/shop/",
    "pages_collected": "catalog pages and book pages",
    "rules": {"robots.txt": "catalog and book pages allowed; "
                            "admin and cart disallowed",
              "crawl_delay_seconds": 1,
              "terms": "learning use; identify yourself; 1 s pause"},
    "personal_data": "none collected",
    "contact": "you@example.com",
    "collected": "2026-10-15"}
```

The record is an ordinary dictionary; saving it and reading it back checks that it survives as JSON:

```python
text = json.dumps(record, indent=2)
Path("source_corner_books.json").write_text(text)
saved = json.loads(Path("source_corner_books.json").read_text())
print(len(saved), "fields; delay:",
      saved["rules"]["crawl_delay_seconds"], "s")
```

Output:

```text
7 fields; delay: 1 s
```

Keeping the record as JSON next to the data makes it easy to read for people and programs alike.

## Exercise 10.6

*List the fields you would collect to study ratings and prices, and those you would leave out.*

To study how ratings relate to price, a minimal dataset needs:

- **Collect:** the title or product code (to identify each book), the price, the rating, the category (prices differ by category), and the publication year (newer books may cost more).

- **Leave out:** the author's name (not needed for the question, and it is personal data about a real person on a real site), the full description (copyrighted text, not needed), and the stock (unrelated to the question).

Collecting only what the question needs is data minimization (Chapter 10): a smaller dataset is faster to collect, puts less load on the site, and carries less legal and ethical risk.

## Exercise 10.7

*Stop after three 429 or 503 responses in a row, and double the delay after each one.*

```python
def careful_get(self, url, max_strikes=3):
    """GET like get(), slowing down when the server pushes back."""
    response = self.get(url)
    if response.status_code in (429, 503):
        self.strikes = getattr(self, "strikes", 0) + 1
        self.delay *= 2
        if self.strikes >= max_strikes:
            raise RuntimeError(f"stopping: {self.strikes} refusals")
    else:
        self.strikes = 0
    return response

ResponsibleFetcher.careful_get = careful_get
```

`getattr(self, "strikes", 0)` reads the counter, or 0 if it doesn't exist yet. Every refusal doubles the delay, and a success resets the count. The rate-limited API endpoint is outside `/shop`, but allowed by `robots.txt`. With the delay set to 0.3 seconds to provoke refusals:

```python
fetcher = ResponsibleFetcher(BASE, "ds-book-crawler",
                             "you@example.com")
fetcher.delay = 0.3
time.sleep(2)
try:
    for n in range(8):
        r = fetcher.careful_get(f"{BASE}/api/v1/limited")
        print(n, r.status_code, round(fetcher.delay, 2))
except RuntimeError as err:
    print(err)
```

Output:

```text
0 200 0.3
1 200 0.3
2 200 0.3
3 429 0.6
4 429 1.2
5 200 1.2
6 200 1.2
7 200 1.2
```

The first three calls succeed; then the server refuses, and each refusal doubles the delay until the pace is slow enough to be served again, without ever reaching three refusals in a row. A fixed, polite delay from the start would have avoided the refusals altogether.

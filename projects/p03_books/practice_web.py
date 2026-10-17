"""Practice web server for Part II of "Python for Data Science".

It runs on your own computer and plays the part of several real websites
and web APIs, so that every example in Chapters 6 to 10 and Projects 2 to 4
works without an internet connection and gives the same answers every time:

    /api/v1/...        a city bike-share API: paginated JSON, an API key,
                       a rate limit, a flaky and a slow endpoint (Chapter 6)
    /v2/...            a development-indicators API in the World Bank's
                       format, serving Gapminder figures (Project 2)
    /v1/archive        a historical weather API in Open-Meteo's format,
                       with generated daily weather (Project 6)
    /shop/...          a bookstore website to scrape: catalog pages, book
                       pages, categories, a login form (Chapters 7, 8, 10)
    /data/...          pages with HTML tables (Chapter 7)
    /js-store/...      a store whose products are loaded by JavaScript
                       (Chapter 9, Project 4)
    /robots.txt        the site's rules for crawlers (Chapter 10)

Start it in a terminal and leave it running while you try the examples:

    python practice_web.py

or start it from Python, in a background thread:

    import practice_web
    practice_web.start()

Everything is generated from fixed random seeds, except the Gapminder data
(gapminder.csv, CC BY 4.0, gapminder.org), which must be in this folder.
Only the Python standard library is used.
"""
import csv
import html
import json
import math
import random
import secrets
import socket
import threading
import time
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

HERE = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", 8020
BASE = f"http://{HOST}:{PORT}"
API_KEY = "demo-key-2026"
USERNAME, PASSWORD = "reader", "open-sesame"


# --------------------------------------------------------------- bike share
STREETS = ["Main St", "Liberty Ave", "Penn Ave", "Forbes Ave", "Butler St",
           "Carson St", "Fifth Ave", "Smallman St", "Grant St", "Ellsworth Ave"]
CROSS = ["1st Ave", "3rd St", "9th St", "12th St", "17th St", "21st St",
         "Market Sq", "Library Way", "River Trail", "Park Pl"]
HOODS = ["Downtown", "Strip District", "Lawrenceville", "Oakland",
         "Shadyside", "South Side", "North Shore"]


def make_stations():
    rng = random.Random(11)
    corners = rng.sample([f"{a} & {b}" for a in STREETS for b in CROSS], 40)
    stations = []
    for n, corner in enumerate(corners, start=1):
        capacity = rng.choice([11, 15, 15, 19, 19, 23, 27])
        bikes = rng.randint(0, capacity)
        stations.append({
            "station_id": f"S{n:03d}",
            "name": corner,
            "neighborhood": rng.choice(HOODS),
            "location": {"lat": round(40.43 + rng.uniform(0, 0.04), 5),
                         "lon": round(-80.01 + rng.uniform(0, 0.07), 5)},
            "capacity": capacity,
            "status": {"bikes_available": bikes,
                       "ebikes_available": rng.randint(0, bikes),
                       "docks_available": capacity - bikes,
                       "is_renting": rng.random() > 0.08},
        })
    return stations


STATIONS = make_stations()


def make_trips(day):
    """All trips of one day; the same day always gives the same trips."""
    rng = random.Random(f"trips-{day}")
    weekend = day.weekday() >= 5
    if weekend:                          # late mornings and afternoons
        weights = [1, 1, 2, 3, 5, 7, 9, 10, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    else:                                # commuting peaks
        weights = [2, 6, 9, 6, 4, 4, 5, 5, 5, 6, 8, 9, 7, 5, 4, 3, 2, 1]
    trips = []
    for _ in range(rng.randint(260, 340) + (60 if weekend else 0)):
        hour = rng.choices(range(6, 24), weights=weights)[0]
        start = datetime(day.year, day.month, day.day, hour,
                         rng.randint(0, 59), rng.randint(0, 59))
        a, b = rng.sample(STATIONS, 2)
        member = rng.random() < (0.45 if weekend else 0.68)
        minutes = rng.lognormvariate(2.4 if member else 2.95, 0.5)
        trips.append({
            "started_at": start.isoformat(),
            "duration_min": round(minutes, 1),
            "start_station": a["station_id"],
            "end_station": b["station_id"],
            "rider": "member" if member else "casual",
            "bike": "electric" if rng.random() < 0.35 else "classic",
        })
    trips.sort(key=lambda t: t["started_at"])
    return [{"trip_id": f"{day:%Y%m%d}-{n:04d}", **t}
            for n, t in enumerate(trips, start=1)]


# ------------------------------------------------- World Bank-format API
INDICATORS = {
    "SP.POP.TOTL": ("Population, total", "pop", 0),
    "SP.DYN.LE00.IN": ("Life expectancy at birth, total (years)",
                       "lifeExp", 1),
    "NY.GDP.PCAP.PP.KD": ("GDP per capita, PPP (constant international $)",
                          "gdpPercap", 0),
}


def load_gapminder():
    path = HERE / "gapminder.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


GAPMINDER = load_gapminder()
COUNTRIES = {}
for _row in GAPMINDER:
    COUNTRIES[_row["iso3"]] = {"id": _row["iso3"], "iso2Code": _row["iso2"],
                               "name": _row["country"],
                               "region": {"value": _row["continent"]}}


# ------------------------------------------------------------- bookstore
CATEGORIES = ["Mystery", "Science Fiction", "Romance", "History", "Travel",
              "Poetry", "Cooking", "Business", "Children", "Fantasy"]
ADJECTIVES = ["Silent", "Golden", "Hidden", "Last", "Broken", "Northern",
              "Quiet", "Distant", "Secret", "Burning", "Painted", "Winter",
              "Forgotten", "Electric", "Gentle", "Restless"]
NOUNS = ["River", "Garden", "Kingdom", "Letter", "Harbor", "Orchard",
         "Machine", "Lantern", "Mountain", "Library", "Station", "Island",
         "Compass", "Kitchen", "Empire", "Bridge"]
FIRST = ["Ada", "Ben", "Clara", "Dev", "Elena", "Farid", "Grace", "Hiro",
         "Ines", "Jonah", "Kavya", "Liam", "Maya", "Noor", "Omar", "Priya",
         "Quinn", "Rosa", "Sam", "Tara"]
LAST = ["Abbott", "Banerjee", "Castillo", "Dubois", "Eriksen", "Fischer",
        "Gallagher", "Hughes", "Iyer", "Jensen", "Kowalski", "Lindqvist",
        "Moreau", "Nakamura", "Okafor", "Petrov"]
SENTENCES = ["A story about second chances.",
             "Told in three parts, across four decades.",
             "The author's most personal book so far.",
             "Readers will not forget the final chapter.",
             "Based on years of research and travel.",
             "Full of practical advice and good humor.",
             "A gripping read from the first page.",
             "Beautifully illustrated throughout."]


def slugify(text):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in text)
    return "-".join(part for part in keep.split("-") if part)


def make_books():
    rng = random.Random(7)
    books, seen = [], set()
    while len(books) < 300:
        pattern = rng.random()
        if pattern < 0.4:
            title = f"The {rng.choice(ADJECTIVES)} {rng.choice(NOUNS)}"
        elif pattern < 0.7:
            title = (f"The {rng.choice(NOUNS)} of the "
                     f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)}")
        else:
            title = (f"{rng.choice(ADJECTIVES)} {rng.choice(NOUNS)}s: "
                     f"A {rng.choice(['Novel', 'Memoir', 'Guide', 'Story'])}")
        if title in seen:
            continue
        seen.add(title)
        n = len(books) + 1
        stock = rng.choice([0, 0, 1, 2, 3, 5, 8, 12, 14, 19, 22])
        books.append({
            "id": n,
            "title": title,
            "slug": f"{slugify(title)}-{n}",
            "author": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            "category": rng.choice(CATEGORIES),
            "price": round(rng.uniform(7.5, 54.99), 2),
            "rating": rng.choices([1, 2, 3, 4, 5],
                                  weights=[1, 2, 4, 5, 3])[0],
            "stock": stock,
            "year": rng.randint(1958, 2026),
            "upc": f"{rng.getrandbits(48):012x}",
            "description": (" ".join(rng.sample(SENTENCES, 2))
                            if rng.random() > 0.1 else ""),
        })
    return books


BOOKS = make_books()
BOOKS_BY_SLUG = {b["slug"]: b for b in BOOKS}
PER_PAGE = 20
ORDERS = [("A-1007", "2026-03-14", 2, 41.48), ("A-1032", "2026-05-02", 1,
                                                  18.99),
          ("A-1088", "2026-08-21", 4, 96.20), ("A-1101", "2026-09-30", 1,
                                                 12.50)]


# -------------------------------------------------------------- JS store
BRANDS = ["Arcwell", "Brightline", "Corvo", "Dunmore", "Everpeak"]
GADGETS = [("Wireless earbuds", "Audio", 59), ("Bluetooth speaker", "Audio",
                                                 45),
           ("Noise-canceling headphones", "Audio", 189),
           ("USB-C charger 65W", "Power", 39), ("Power bank 20000mAh",
                                                  "Power", 49),
           ("Smart plug (2-pack)", "Home", 25), ("Video doorbell", "Home",
                                                 119),
           ("Fitness tracker", "Wearables", 79), ("Smartwatch", "Wearables",
                                                  229),
           ("Mechanical keyboard", "Computing", 99), ("Webcam 1080p",
                                                      "Computing", 54),
           ("Portable SSD 1TB", "Computing", 109)]


def make_products():
    rng = random.Random(3)
    products = []
    for n, (gadget, category, base) in enumerate(GADGETS * 5, start=1):
        brand = BRANDS[(n - 1) // len(GADGETS)]
        products.append({
            "id": n, "name": f"{brand} {gadget}", "brand": brand,
            "category": category,
            "base_price": round(base * rng.uniform(0.8, 1.3), 2),
            "rating": round(rng.uniform(3.1, 4.9), 1),
            "reviews": rng.randint(4, 2400),
        })
    return products


PRODUCTS = make_products()


def price_on(product, day):
    """A product's price on a day: small daily swings, occasional sales."""
    rng = random.Random(f"{product['id']}-{day}")
    factor = 1 + 0.04 * math.sin(day.toordinal() / 3 + product["id"])
    if rng.random() < 0.12:
        factor *= 0.8                       # a 20% sale
    return round(product["base_price"] * factor, 2)


# ------------------------------------------------- Open-Meteo-format API
# Daily weather is generated, not measured: each place has a climate (the
# normal daily high and its yearly swing, the day-to-day range, how often
# and how much it rains by month), plus random weather around it and a slow
# warming trend. Three cities have climates modeled on their real ones; any
# other place gets a rough climate from its latitude.
WX_FIRST, WX_LAST = date(2000, 1, 1), date(2026, 9, 30)   # data available
WX_VARIABLES = {"temperature_2m_max": "°C", "temperature_2m_min": "°C",
                "temperature_2m_mean": "°C", "precipitation_sum": "mm"}
WX_CLIMATES = {   # high, swing, range, sd, wet chance by month, mean rain
    (40.44, -80.0): (16.6, 12.6, 10.4, 3.8,
                     [.45, .42, .45, .45, .45, .42, .38, .35, .33, .33,
                      .40, .45], 6.4, 235),
    (33.45, -112.07): (30.4, 10.6, 14.2, 2.4,
                       [.10, .10, .08, .04, .02, .02, .13, .15, .08, .05,
                        .05, .09], 6.0, 331),
    (47.61, -122.33): (15.9, 8.6, 7.6, 2.7,
                       [.62, .55, .58, .48, .38, .30, .14, .16, .27, .48,
                        .65, .63], 5.4, 52),
}
WX_CACHE = {}


def wx_climate(lat, lon):
    for (clat, clon), climate in WX_CLIMATES.items():
        if abs(lat - clat) < 0.3 and abs(lon - clon) < 0.3:
            return climate
    a = abs(lat)
    high = 31 - 0.45 * max(a - 25, 0) if a > 25 else 31
    return (high, min(2 + 0.35 * a, 18), 9.0, 3.0, [0.35] * 12, 6.0, 100)


def wx_series(lat, lon):
    """Daily weather from WX_FIRST to WX_LAST for one place, always the
    same for the same coordinates."""
    key = (round(lat, 2), round(lon, 2))
    if key in WX_CACHE:
        return WX_CACHE[key]
    high, swing, spread, sd, wet, rain, elevation = wx_climate(*key)
    south = -1 if lat < 0 else 1
    rng = random.Random(f"weather-{key[0]:.2f}-{key[1]:.2f}")
    year_shift = {y: rng.gauss(0, 0.3) for y in range(2000, 2027)}
    days, anomaly, was_wet = {}, 0.0, False
    day = WX_FIRST
    while day <= WX_LAST:
        doy = day.timetuple().tm_yday
        season = math.cos(2 * math.pi * (doy - 200) / 365.25) * south
        trend = 0.032 * (day.year - 2000 + doy / 365.25)
        winter = 1.25 if season < 0 else 0.85    # winter is more variable
        anomaly = 0.72 * anomaly + rng.gauss(0, sd * winter * 0.6)
        chance = wet[day.month - 1] + (0.2 if was_wet else 0)
        was_wet = rng.random() < min(chance, 0.9)
        precip = round(rng.gammavariate(0.75, rain / 0.75), 1) if was_wet \
            else 0.0
        tmax = (high + swing * season + trend + year_shift[day.year]
                + anomaly - (1.6 if was_wet else 0))
        if key == (47.61, -122.33) and date(2021, 6, 25) <= day \
                <= date(2021, 6, 29):              # the 2021 heat dome
            tmax += [9, 14, 18, 20, 11][(day - date(2021, 6, 25)).days]
        tmin = tmax - spread * (0.65 if was_wet else 1) + rng.gauss(0, 1.2)
        days[day] = (round(tmax, 1), round(tmin, 1),
                     round((tmax + tmin) / 2, 1), precip)
        day += timedelta(days=1)
    WX_CACHE[key] = (days, elevation)
    return WX_CACHE[key]


TIMEZONES = {"GMT": ("GMT", 0), "UTC": ("UTC", 0),
             "America/New_York": ("EST", -18000),
             "America/Phoenix": ("MST", -25200),
             "America/Los_Angeles": ("PST", -28800)}


# ------------------------------------------------------------------- pages
def page(title, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{html.escape(title)}</title></head>
<body>
<header><a href="/shop/">Corner Books</a></header>
<main>
{body}
</main>
<footer><p>Practice site for "Python for Data Science".
<a href="/shop/terms.html">Terms of use</a></p></footer>
</body>
</html>
"""


def stars(n):
    return "★" * n + "☆" * (5 - n)


def book_card(book):
    short = book["title"] if len(book["title"]) <= 28 \
        else book["title"][:26] + "…"
    stock = ('<p class="stock in-stock">In stock</p>' if book["stock"]
             else '<p class="stock out-of-stock">Out of stock</p>')
    url = f"/shop/book/{book['slug']}.html"
    return f"""<article class="book">
  <h3><a href="{url}" title="{html.escape(book['title'])}">{html.escape(short)}</a></h3>
  <p class="author">by {html.escape(book['author'])}</p>
  <p class="stars stars-{book['rating']}" aria-label="{book['rating']} out of 5 stars">{stars(book['rating'])}</p>
  <p class="price">${book['price']:.2f}</p>
  {stock}
</article>"""


def sidebar():
    items = "\n".join(
        f'  <li><a href="/shop/category/{slugify(c)}/page-1.html">{c}</a>'
        f' ({sum(b["category"] == c for b in BOOKS)})</li>'
        for c in CATEGORIES)
    return f'<nav><h2>Categories</h2>\n<ul class="categories">\n{items}\n</ul></nav>'


def listing(books, number, title):
    pages = max(1, math.ceil(len(books) / PER_PAGE))
    if not 1 <= number <= pages:
        return None
    chunk = books[(number - 1) * PER_PAGE:number * PER_PAGE]
    cards = "\n".join(book_card(b) for b in chunk)
    pager = ['<ul class="pager">']
    if number > 1:
        pager.append(f'  <li class="previous"><a href="page-{number - 1}'
                     '.html">previous</a></li>')
    pager.append(f'  <li class="current">Page {number} of {pages}</li>')
    if number < pages:
        pager.append(f'  <li class="next"><a href="page-{number + 1}'
                     '.html">next</a></li>')
    pager.append("</ul>")
    body = (f"<h1>{html.escape(title)}</h1>\n{sidebar()}\n"
            f'<p class="results">{len(books)} books</p>\n'
            f'<section class="books">\n{cards}\n</section>\n'
            + "\n".join(pager))
    return page(f"{title} | Corner Books", body)


def book_page(book):
    if book["stock"]:
        availability = f"In stock ({book['stock']} available)"
    else:
        availability = "Out of stock"
    category = (f'<a href="/shop/category/{slugify(book["category"])}'
                f'/page-1.html">{book["category"]}</a>')
    rows = [("UPC", book["upc"]), ("Category", category),
            ("Price", f"${book['price']:.2f}"),
            ("Availability", availability), ("Published", book["year"])]
    table = "\n".join(f"  <tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    desc = (f'<div id="description"><h2>Description</h2>\n'
            f'<p>{book["description"]}</p></div>'
            if book["description"] else "")
    body = f"""<ul class="breadcrumb"><li><a href="/shop/">Home</a></li>
<li>{category}</li><li class="active">{html.escape(book['title'])}</li></ul>
<article class="product">
<h1>{html.escape(book['title'])}</h1>
<p class="author">by {html.escape(book['author'])}</p>
<p class="stars stars-{book['rating']}">{stars(book['rating'])}</p>
<table id="product-info">
{table}
</table>
{desc}
</article>"""
    return page(f"{book['title']} | Corner Books", body)


ROBOTS = """# Corner Books practice site
User-agent: *
Disallow: /shop/admin/
Disallow: /shop/cart
Crawl-delay: 1

User-agent: GreedyBot
Disallow: /

Sitemap: http://127.0.0.1:8020/sitemap.xml
"""

TERMS = page("Terms of use | Corner Books", """<h1>Terms of use</h1>
<p>You may browse and copy information from this practice site for learning.
Automated access is welcome if it follows robots.txt, waits at least one
second between requests and identifies itself with a User-Agent header that
includes a way to contact you.</p>""")


def table_page():
    rows = [r for r in GAPMINDER if r["year"] == "2007"]
    parts = ["<h1>Life expectancy and income, 2007</h1>",
             "<p>Source: Gapminder (gapminder.org), CC BY 4.0.</p>"]
    for continent in sorted({r["continent"] for r in rows}):
        sub = sorted((r for r in rows if r["continent"] == continent),
                     key=lambda r: -float(r["lifeExp"]))
        body = "\n".join(
            f"<tr><td>{html.escape(r['country'])}</td>"
            f"<td>{float(r['lifeExp']):.1f}</td>"
            f"<td>{int(r['pop']):,}</td>"
            f"<td>${float(r['gdpPercap']):,.0f}</td></tr>" for r in sub)
        parts.append(f'<h2>{continent}</h2>\n<table class="data">\n'
                     "<thead><tr><th>Country</th><th>Life expectancy</th>"
                     "<th>Population</th><th>GDP per person</th></tr>"
                     f"</thead>\n<tbody>\n{body}\n</tbody>\n</table>")
    return page("Life expectancy, 2007", "\n".join(parts))


def sitemap():
    pages = math.ceil(len(BOOKS) / PER_PAGE)
    urls = [f"{BASE}/shop/catalogue/page-{n}.html" for n in range(1, pages + 1)]
    urls += [f"{BASE}/shop/book/{b['slug']}.html" for b in BOOKS]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns='
            '"http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{body}\n</urlset>\n")


def login_page(token, error=""):
    message = f'<p class="error">{error}</p>' if error else ""
    return page("Log in | Corner Books", f"""<h1>Log in</h1>
{message}
<form method="post" action="/shop/login" id="login-form">
  <input type="hidden" name="csrf_token" value="{token}">
  <label>Username <input name="username"></label>
  <label>Password <input name="password" type="password"></label>
  <button type="submit">Log in</button>
</form>""")


def account_page(user):
    rows = "\n".join(f"<tr><td>{o}</td><td>{d}</td><td>{n}</td>"
                     f"<td>${t:.2f}</td></tr>" for o, d, n, t in ORDERS)
    return page("Your account | Corner Books", f"""<h1>Hello, {user}</h1>
<h2>Your orders</h2>
<table id="orders">
<thead><tr><th>Order</th><th>Date</th><th>Items</th><th>Total</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
<p><a href="/shop/logout">Log out</a></p>""")


JS_STORE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Gadget Store</title>
<style>.product{border:1px solid #ccc;margin:4px;padding:4px}</style></head>
<body>
<h1>Gadget Store</h1>
<p id="status">Loading products...</p>
<div id="products"></div>
<button id="load-more" hidden>Load more</button>
<script>
const day = new URLSearchParams(location.search).get("day") || "";
let page = 1;
async function load() {
  const url = `/api/store/products?page=${page}&per_page=12&day=${day}`;
  const data = await (await fetch(url)).json();
  for (const p of data.products) {
    const card = document.createElement("div");
    card.className = "product";
    card.dataset.id = p.id;
    card.innerHTML = `<h2 class="name">${p.name}</h2>
      <span class="category">${p.category}</span>
      <span class="price">$${p.price.toFixed(2)}</span>
      <span class="rating">${p.rating} (${p.reviews} reviews)</span>`;
    document.getElementById("products").append(card);
  }
  const shown = document.querySelectorAll(".product").length;
  document.getElementById("status").textContent =
    `Showing ${shown} of ${data.total} products`;
  document.getElementById("load-more").hidden = !data.has_more;
  page += 1;
}
document.getElementById("load-more").addEventListener("click", load);
setTimeout(load, 500);
</script>
</body>
</html>
"""

JS_FEED = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Gadget Store: all products</title>
<style>.product{height:120px;border:1px solid #ccc;margin:4px}</style>
</head>
<body>
<h1>All products</h1>
<div id="products"></div>
<p id="end" hidden>You've reached the end.</p>
<div id="sentinel" style="height:10px"></div>
<script>
let page = 1, busy = false, done = false;
async function more() {
  if (busy || done) return;
  busy = true;
  const r = await fetch(`/api/store/products?page=${page}&per_page=12`);
  const data = await r.json();
  for (const p of data.products) {
    const card = document.createElement("div");
    card.className = "product";
    card.innerHTML = `<h2 class="name">${p.name}</h2>
      <span class="price">$${p.price.toFixed(2)}</span>`;
    document.getElementById("products").append(card);
  }
  done = !data.has_more;
  document.getElementById("end").hidden = !done;
  page += 1;
  busy = false;
}
new IntersectionObserver(entries => {
  if (entries[0].isIntersecting) more();
}).observe(document.getElementById("sentinel"));
</script>
</body>
</html>
"""


# ----------------------------------------------------------------- handler
class State:
    """Counters shared by all requests (the server is multi-threaded)."""
    lock = threading.Lock()
    flaky_calls = 0
    limited = []                         # times of recent /limited calls
    page7_failed = False
    sessions = {}                        # session id -> user name
    csrf = set()
    hits = []                            # (time, path, user agent)


class Handler(BaseHTTPRequestHandler):
    server_version = "PracticeWeb/1.0"

    def log_message(self, *args):        # keep the terminal quiet
        pass

    # ----- helpers
    def send(self, status, body, kind="text/html; charset=utf-8",
             headers=None):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass                     # the client stopped waiting

    def json(self, status, obj, headers=None):
        self.send(status, json.dumps(obj, indent=1),
                  "application/json; charset=utf-8", headers)

    def cookies(self):
        jar = {}
        for part in self.headers.get("Cookie", "").split(";"):
            name, _, value = part.strip().partition("=")
            if name:
                jar[name] = value
        return jar

    # ----- dispatch
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url = urlsplit(self.path)
        query = {k: v[-1] for k, v in parse_qs(url.query).items()}
        path = url.path
        with State.lock:
            State.hits.append((time.time(), path,
                               self.headers.get("User-Agent", "")))
        if path.startswith("/api/v1/"):
            return self.bike_api(path, query)
        if path.startswith("/v2/"):
            return self.indicators_api(path, query)
        if path == "/v1/archive":
            return self.weather_api(query)
        if path.startswith("/api/store/"):
            return self.store_api(path, query)
        if path == "/sitemap.xml":
            return self.send(200, sitemap(), "application/xml; charset=utf-8")
        if path == "/robots.txt":
            return self.send(200, ROBOTS, "text/plain; charset=utf-8")
        if path in ("/shop", "/shop/", "/shop/index.html"):
            return self.send(200, listing(BOOKS, 1, "All books"))
        if path.startswith("/shop/"):
            return self.shop(path, query)
        if path == "/data/life-expectancy-2007.html":
            return self.send(200, table_page())
        if path in ("/js-store", "/js-store/", "/js-store/index.html"):
            return self.send(200, JS_STORE)
        if path == "/js-store/feed.html":
            return self.send(200, JS_FEED)
        if path in ("", "/"):
            return self.send(200, page("Practice site", "<h1>Practice site"
                                       "</h1><p>See /shop/, /api/v1/stations"
                                       " and /js-store/.</p>"))
        self.send(404, page("Not found", "<h1>404: page not found</h1>"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = {k: v[-1] for k, v in
                parse_qs(self.rfile.read(length).decode()).items()}
        if urlsplit(self.path).path == "/shop/login":
            return self.login(form)
        self.send(405, page("Not allowed", "<h1>405: method not allowed</h1>"))

    # ----- bike share
    def bike_api(self, path, query):
        if path == "/api/v1/stations":
            per_page = min(int(query.get("per_page", 10)), 50)
            number = int(query.get("page", 1))
            pages = math.ceil(len(STATIONS) / per_page)
            chunk = STATIONS[(number - 1) * per_page:number * per_page]
            nxt = (f"{BASE}/api/v1/stations?"
                   + urlencode({"page": number + 1, "per_page": per_page})
                   if number < pages else None)
            return self.json(200, {
                "data": chunk,
                "meta": {"page": number, "per_page": per_page,
                         "pages": pages, "total": len(STATIONS)},
                "links": {"next": nxt}})
        if path == "/api/v1/trips":
            if self.headers.get("X-API-Key") != API_KEY:
                return self.json(401, {"error": "missing or invalid API "
                                                "key; send it in the "
                                                "X-API-Key header"})
            try:
                day = date.fromisoformat(query.get("date", ""))
            except ValueError:
                return self.json(400, {"error": "give a date as "
                                                "YYYY-MM-DD"})
            trips = make_trips(day)
            per_page = min(int(query.get("per_page", 100)), 200)
            number = int(query.get("page", 1))
            chunk = trips[(number - 1) * per_page:number * per_page]
            return self.json(200, {
                "data": chunk,
                "meta": {"date": day.isoformat(), "page": number,
                         "per_page": per_page, "total": len(trips),
                         "pages": math.ceil(len(trips) / per_page)}})
        if path == "/api/v1/limited":
            now = time.time()
            with State.lock:
                State.limited = [t for t in State.limited if now - t < 2]
                if len(State.limited) >= 3:
                    return self.json(429, {"error": "rate limit: 3 "
                                                    "requests per 2 "
                                                    "seconds"},
                                     {"Retry-After": "2"})
                State.limited.append(now)
            return self.json(200, {"ok": True, "served_at":
                                   datetime.now().strftime("%H:%M:%S")})
        if path == "/api/v1/flaky":
            with State.lock:
                State.flaky_calls += 1
                fail = State.flaky_calls % 3 != 0
            if fail:
                return self.json(503, {"error": "service busy, try again"})
            return self.json(200, {"ok": True, "message": "worked this time"})
        if path == "/api/v1/slow":
            time.sleep(float(query.get("seconds", 3)))
            return self.json(200, {"ok": True})
        self.json(404, {"error": f"no such endpoint: {path}"})

    # ----- World Bank format
    def indicators_api(self, path, query):
        if query.get("format") != "json":
            xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
                   '<wb:data xmlns:wb="http://www.worldbank.org">\n'
                   "  <!-- add format=json to get JSON -->\n</wb:data>\n")
            return self.send(200, xml, "application/xml; charset=utf-8")
        parts = path.strip("/").split("/")
        per_page = int(query.get("per_page", 50))
        number = int(query.get("page", 1))
        if parts == ["v2", "country"]:
            rows = sorted(COUNTRIES.values(), key=lambda c: c["id"])
        elif (len(parts) == 5 and parts[1] == "country"
              and parts[3] == "indicator"):
            if parts[4] not in INDICATORS:
                return self.json(200, [{"message": [{
                    "id": "120", "key": "Invalid value",
                    "value": "The provided parameter value is not "
                             "valid"}]}])
            rows = self.indicator_rows(parts[2], parts[4],
                                       query.get("date", ""))
        else:
            return self.json(404, [{"message": [{
                "id": "160", "key": "Not found",
                "value": "No such endpoint on the practice server"}]}])
        pages = max(1, math.ceil(len(rows) / per_page))
        meta = {"page": number, "pages": pages, "per_page": per_page,
                "total": len(rows), "sourceid": "2",
                "lastupdated": "2026-07-01"}
        chunk = rows[(number - 1) * per_page:number * per_page]
        self.json(200, [meta, chunk])

    def indicator_rows(self, codes, indicator, dates):
        name, column, decimals = INDICATORS[indicator]
        wanted = {c.upper() for c in codes.split(";")}
        if "ALL" in wanted:
            wanted = set(COUNTRIES)
        wanted = {c for c in COUNTRIES if c in wanted
                  or COUNTRIES[c]["iso2Code"] in wanted}
        first, _, last = dates.partition(":")
        first = int(first or 0)
        last = int(last or (first if dates and ":" not in dates else 9999))
        rows = []
        for r in GAPMINDER:
            year = int(r["year"])
            if r["iso3"] in wanted and first <= year <= last:
                value = round(float(r[column]), decimals)
                rows.append({
                    "indicator": {"id": indicator, "value": name},
                    "country": {"id": r["iso2"], "value": r["country"]},
                    "countryiso3code": r["iso3"], "date": r["year"],
                    "value": int(value) if decimals == 0 else value,
                    "unit": "", "obs_status": "", "decimal": decimals})
        rows.sort(key=lambda d: (d["countryiso3code"], -int(d["date"])))
        return rows

    # ----- Open-Meteo format
    def weather_api(self, query):
        def error(reason):
            return self.json(400, {"error": True, "reason": reason})
        try:
            lat, lon = float(query["latitude"]), float(query["longitude"])
        except (KeyError, ValueError):
            return error("Parameter 'latitude' and 'longitude' must be "
                         "numbers")
        try:
            first = date.fromisoformat(query["start_date"])
            last = date.fromisoformat(query["end_date"])
        except (KeyError, ValueError):
            return error("Parameter 'start_date' and 'end_date' must be "
                         "dates in the format yyyy-mm-dd")
        if last < first:
            return error("End-date must be larger or equal than "
                         "start-date")
        if first < WX_FIRST:
            return error(f"Parameter 'start_date' is out of allowed range "
                         f"from {WX_FIRST} to {WX_LAST}")
        names = [n for n in query.get("daily", "").split(",") if n]
        for n in names:
            if n not in WX_VARIABLES:
                return error(f"Cannot initialize WeatherVariable from "
                             f"invalid String value {n}.")
        zone = query.get("timezone", "GMT")
        abbr, offset = TIMEZONES.get(zone, (zone, 0))
        days, elevation = wx_series(lat, lon)
        dates = [first + timedelta(days=i)
                 for i in range((last - first).days + 1)]
        column = list(WX_VARIABLES).index
        daily = {"time": [d.isoformat() for d in dates]}
        for n in names:
            daily[n] = [days[d][column(n)] if d in days else None
                        for d in dates]
        self.json(200, {
            "latitude": round(lat * 4) / 4 + 0.0, "longitude":
            round(lon * 4) / 4 + 0.0, "generationtime_ms": 0.42,
            "utc_offset_seconds": offset, "timezone": zone,
            "timezone_abbreviation": abbr, "elevation": float(elevation),
            "daily_units": {"time": "iso8601",
                            **{n: WX_VARIABLES[n] for n in names}},
            "daily": daily})

    # ----- JS store API
    def store_api(self, path, query):
        if path != "/api/store/products":
            return self.json(404, {"error": "no such endpoint"})
        try:
            day = date.fromisoformat(query.get("day") or "2026-10-01")
        except ValueError:
            day = date(2026, 10, 1)
        per_page = min(int(query.get("per_page", 12)), 60)
        number = int(query.get("page", 1))
        chunk = PRODUCTS[(number - 1) * per_page:number * per_page]
        time.sleep(0.3)                    # a slow-ish backend
        products = [{"id": p["id"], "name": p["name"], "brand": p["brand"],
                     "category": p["category"], "price": price_on(p, day),
                     "rating": p["rating"], "reviews": p["reviews"]}
                    for p in chunk]
        self.json(200, {"products": products, "page": number,
                        "total": len(PRODUCTS),
                        "has_more": number * per_page < len(PRODUCTS)})

    # ----- bookstore
    def shop(self, path, query):
        if path == "/shop/terms.html":
            return self.send(200, TERMS)
        if path.startswith("/shop/catalogue/page-"):
            number = int(path.rsplit("-", 1)[1].split(".")[0])
            if number == 7:
                with State.lock:
                    first_time = not State.page7_failed
                    State.page7_failed = True
                if first_time:            # fails once, then works
                    return self.send(503, page("Busy", "<h1>503: try again"
                                               "</h1>"),
                                     headers={"Retry-After": "1"})
            body = listing(BOOKS, number, "All books")
            if body:
                return self.send(200, body)
        if path.startswith("/shop/category/"):
            parts = path.split("/")
            names = {slugify(c): c for c in CATEGORIES}
            if len(parts) == 5 and parts[3] in names:
                cat = names[parts[3]]
                number = int(parts[4].split("-")[1].split(".")[0])
                body = listing([b for b in BOOKS if b["category"] == cat],
                               number, cat)
                if body:
                    return self.send(200, body)
        if path.startswith("/shop/book/"):
            slug = path[len("/shop/book/"):].removesuffix(".html")
            if slug in BOOKS_BY_SLUG:
                return self.send(200, book_page(BOOKS_BY_SLUG[slug]))
        if path == "/shop/login":
            token = secrets.token_hex(8)
            with State.lock:
                State.csrf.add(token)
            return self.send(200, login_page(token),
                             headers={"Set-Cookie": f"csrftoken={token}; "
                                                    "Path=/; HttpOnly"})
        if path == "/shop/account":
            user = State.sessions.get(self.cookies().get("sessionid"))
            if not user:
                return self.send(302, "", headers={
                    "Location": "/shop/login?next=/shop/account"})
            return self.send(200, account_page(user))
        if path == "/shop/logout":
            State.sessions.pop(self.cookies().get("sessionid"), None)
            return self.send(302, "", headers={"Location": "/shop/"})
        if path.startswith("/shop/admin"):
            return self.send(403, page("Forbidden", "<h1>403: forbidden"
                                       "</h1>"))
        self.send(404, page("Not found", "<h1>404: page not found</h1>"))

    def login(self, form):
        token = form.get("csrf_token", "")
        if (token not in State.csrf
                or self.cookies().get("csrftoken") != token):
            return self.send(403, page("Forbidden", "<h1>403: the form has "
                                       "expired; reload the login page"
                                       "</h1>"))
        if (form.get("username"), form.get("password")) != (USERNAME,
                                                            PASSWORD):
            new = secrets.token_hex(8)
            with State.lock:
                State.csrf.add(new)
            return self.send(200, login_page(new, "Wrong user name or "
                                             "password."),
                             headers={"Set-Cookie": f"csrftoken={new}; "
                                                    "Path=/; HttpOnly"})
        session = secrets.token_hex(16)
        with State.lock:
            State.sessions[session] = USERNAME
        self.send(303, "", headers={
            "Location": "/shop/account",
            "Set-Cookie": f"sessionid={session}; Path=/; HttpOnly"})


# ------------------------------------------------------------------- start
def running():
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex((HOST, PORT)) == 0


def start():
    """Start the server in a background thread, unless it already runs."""
    if running():
        return BASE
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    for _ in range(50):
        if running():
            break
        time.sleep(0.05)
    return BASE


if __name__ == "__main__":
    print(f"Practice server running at {BASE}  (Ctrl+C to stop)")
    try:
        ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        pass

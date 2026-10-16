# Python for Data Science: companion code

The code and data for **Python for Data Science: Collect, Clean, Analyze and
Visualize Real-World Data** by Vamsi Krishna Kandala, Book 2 of the
*Python for…* series.

Every listing in the book is here exactly as printed, with the datasets it
reads.

| Folder | Contents |
|---|---|
| `chapters/` | One folder per chapter, for example `ch03_pandas/`, with a `data/` folder holding the files that chapter reads |
| `projects/` | One folder per project, for example `p01_spending/`, with its data |
| `solutions/` | Worked solutions to each chapter's exercises |
| `requirements.txt` | Every package the book uses, at the versions it was tested with |

Each folder holds the same code twice: as a plain Python script (`.py`) and as a
Jupyter notebook (`.ipynb`) with the book's section headings.

## Getting started

You need Python 3.14 or newer. Create a virtual environment and install the
packages (Chapter 1 explains each step):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run a chapter's code from its own folder, so that paths such as
`data/penguins.csv` work exactly as printed in the book:

```bash
cd chapters/ch03_pandas
python ch03_pandas.py
```

Or start JupyterLab with `python -m jupyter lab` and open the chapter's
notebook. On macOS and Linux, type `python3` instead of `python` if `python`
is not found.

## The datasets

| File | Source | License |
|---|---|---|
| `penguins.csv` | Palmer Penguins: Gorman, Williams and Fraser, Palmer Station LTER; published by Horst, Hill and Gorman | CC0 |
| `chinook.sqlite` | Chinook sample database, Luis Rocha | MIT |
| `gapminder.csv` (Part II folders, served by `practice_web.py`) | Gapminder Foundation, gapminder.org | CC BY 4.0 |
| `transactions.csv`, `store_sales.xlsx`, `orders.json` | Created for this book | Free to use |
| `shop_orders_raw.csv`, `shop_orders.parquet`, `shop_customers.csv`, `support_tickets.csv` (Part III) | Created for this book: a fictional coffee shop | Free to use |
| `service_requests.csv`, `agencies.csv`, `districts.csv` (Project 5) | Created for this book, modeled on cities' open 311 data | Free to use |

## Part II: the practice server

Chapters 6 to 10 and Projects 2 to 4 talk to `practice_web.py`, a small web
server that runs on your own computer and plays the part of a bike-share API,
a development-indicators API, an online bookstore and a JavaScript store. Each
Part II folder has its own copy. The book's code starts it in the background
with `practice_web.start()`; you can also run `python practice_web.py` in a
second terminal. Chapter 9 drives a real browser: install it once with
`python -m playwright install chromium`, and run that chapter's code, and
Project 4's, as a script rather than in a notebook (see the note in the
chapter).

## Part IV: interactive charts

Chapter 17's Plotly charts open in your browser or notebook. Saving them as
pictures uses Kaleido, which needs Chrome; if you don't have it, run
`plotly_get_chrome` once after installing the requirements.

## Checking everything

`run_all.py` runs every script in the repository and reports any that fail:

```bash
python run_all.py            # everything
python run_all.py ch04       # only the scripts whose path contains "ch04"
```

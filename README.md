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
| `service_requests.csv`, `agencies.csv`, `districts.csv` (Project 7) | Created for this book, modeled on cities' open 311 data | Free to use |
| `apartments.csv`, `ab_checkout.csv`, `bike_daily.csv` (Parts IV and V) | Created for this book | Free to use |
| `trailhead.sqlite` (Project 10), `ab_signup.csv` (Project 11) | Created for this book: a fictional wholesaler and a fictional app | Free to use |
| `fitness_export.json` (Project 2), `movies.sqlite` (Project 3) | Created for this book: a fictional fitness app and film-rating site | Free to use |
| `survey_raw.csv`, `customer_ages.csv` (Project 8), `subscriptions.csv`, `marketing_spend.csv` (Project 12) | Created for this book: the fictional coffee shop and a fictional language app | Free to use |

Three datasets are made when you run the code: the rides of Chapter 22 and of
Project 13 (`make_rides.py`, about 100 MB in `projects/p13_bikeshare/rides/`),
the weather of Project 9 and the job postings of Project 14, which the practice
server generates.

## The practice server

Chapters 6 to 10 and Projects 4, 5, 6, 9, 14 and 15 talk to `practice_web.py`, a
small web server that runs on your own computer and plays the part of a
bike-share API, a development-indicators API, a weather archive API, an online
bookstore and a JavaScript store. Each folder that uses it has its own copy. The book's code starts it in the background
with `practice_web.start()`; you can also run `python practice_web.py` in a
second terminal.

Chapters 9 and 23 and Projects 6 and 15 drive a real browser with
Playwright: install it once with `python -m playwright install chromium`, and
run their code as scripts rather than in a notebook, because Playwright's
synchronous API can't run inside Jupyter's event loop (Chapter 9 explains).

## Project 15: a pipeline and a dashboard

`projects/p15_dashboard/` holds two programs besides the walkthrough:
`pipeline.py` loads the last four weeks of trips into `bikes.sqlite`, and
`dashboard.py` shows them. With the practice server running in another
terminal:

```bash
python pipeline.py
streamlit run dashboard.py
```

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

## Feedback and errata

Found a mistake, a program that doesn't run as described, or something that
could be explained better? Please tell me:

- **Report a problem:** [open an issue](https://github.com/osv-solutions/python-for-data-science/issues/new/choose),
  with the page or listing number.
- **Ask a question or share an idea:** use the **Discussions** tab.
- **Anything private** (for example, using the book in a course):
  email pythonforseries@osvsolutions.com.

Confirmed corrections are listed in [ERRATA.md](ERRATA.md) and fixed in later
printings.

## The Python for… series

*Python for Data Science* is Book 2 of the *Python for…* series. Each book takes
one field, with the same layout, fully tested code and complete projects. On
Amazon, search for "Python for… series" to see every book released so far.
Titles and order of the planned books may change.

| # | Title | Status |
|---|---|---|
| 1 | Python for All | Available now on Amazon |
| 2 | Python for Data Science | This book |
| 3 | Python for Machine Learning | Coming soon |
| 4 | Python for Deep Learning | Coming soon |
| 5 | Python for Office Automation | Planned |
| 6 | Python for Generative AI and Agentic AI | Planned |
| 7 | Python for Data Engineering | Planned |
| 8 | Python for DevOps and Automation | Planned |
| 9 | Python for Network Automation | Planned |
| 10 | Python for Testing and QA | Planned |
| 11 | Python for Cloud (AWS) | Planned |
| 12 | Python for MLOps | Planned |
| 13 | Python for NLP | Planned |
| 14 | Python for Computer Vision | Planned |
| 15 | Python for IoT: Raspberry Pi, Arduino and ESP32 | Planned |
| 16 | Python for Robotics | Planned |
| 17 | Python for Web Development | Planned |
| 18 | Python for Desktop Applications (Tkinter and PySide6) | Planned |
| 19 | Clean Python: Best Practices and Design Patterns | Planned |
| 20 | Python for Cyber Security and Ethical Hacking | Planned |
| 21 | Python for Healthcare Data | Planned |
| 22 | Python for Finance and Trading | Planned |
| 23 | Python for Kids | Planned |
| 24 | Python for Game Development | Planned |
| 25 | Python Interview Prep | Planned |

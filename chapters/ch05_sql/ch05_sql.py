"""Chapter 5: Data from SQL Databases

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch05_sql.py

or open the notebook and run the cells in order.
"""

# %% 5.2 Exploring an unfamiliar database
import sqlite3
import pandas as pd

con = sqlite3.connect("data/chinook.sqlite")
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type = 'table'", con)
names = tables["name"].tolist()
print(len(names), "tables:", ", ".join(names[:6]))
print(", ".join(names[6:]))

# %% 5.2 Exploring an unfamiliar database
cols = pd.read_sql_query("PRAGMA table_info(Invoice)", con)
print(cols[["name", "type"]].to_string(index=False))
print(pd.read_sql_query("SELECT COUNT(*) AS invoices FROM Invoice",
                        con))

# %% 5.3 Selecting, filtering and sorting
query = """
SELECT Name, Milliseconds / 60000.0 AS minutes
FROM Track
WHERE GenreId = 1 AND Composer IS NOT NULL
ORDER BY Milliseconds DESC
LIMIT 5
"""
longest = pd.read_sql_query(query, con)
print(longest.round(1))

# %% 5.4 Aggregating with GROUP BY
query = """
SELECT BillingCountry AS country,
       COUNT(*) AS invoices,
       ROUND(SUM(Total), 2) AS revenue
FROM Invoice
GROUP BY BillingCountry
ORDER BY revenue DESC
LIMIT 5
"""
print(pd.read_sql_query(query, con))

# %% 5.4 Aggregating with GROUP BY
query = """
SELECT BillingCountry AS country, ROUND(AVG(Total), 2) AS avg_invoice
FROM Invoice
WHERE InvoiceDate >= '2012-01-01'
GROUP BY BillingCountry
HAVING COUNT(*) >= 10
ORDER BY avg_invoice DESC
"""
print(pd.read_sql_query(query, con))

# %% 5.5 Joining tables
query = """
SELECT g.Name AS genre,
       SUM(il.UnitPrice * il.Quantity) AS revenue,
       COUNT(DISTINCT il.TrackId) AS tracks_sold
FROM InvoiceLine AS il
JOIN Track AS t ON il.TrackId = t.TrackId
JOIN Genre AS g ON t.GenreId = g.GenreId
GROUP BY g.Name
ORDER BY revenue DESC
LIMIT 5
"""
print(pd.read_sql_query(query, con).round(2))

# %% 5.5 Joining tables
query = """
SELECT COUNT(*) AS never_sold
FROM Track AS t
LEFT JOIN InvoiceLine AS il ON t.TrackId = il.TrackId
WHERE il.InvoiceLineId IS NULL
"""
print(pd.read_sql_query(query, con))

# %% 5.6 SQL or pandas?
monthly_sql = pd.read_sql_query("""
    SELECT strftime('%Y-%m', InvoiceDate) AS month,
           SUM(Total) AS revenue
    FROM Invoice GROUP BY month ORDER BY month""", con)
invoices = pd.read_sql_query("SELECT * FROM Invoice", con,
                             parse_dates=["InvoiceDate"])
month = invoices["InvoiceDate"].dt.strftime("%Y-%m")
monthly_pd = invoices.groupby(month)["Total"].sum()
print(monthly_sql.tail(3))
same = monthly_sql["revenue"].round(2).values == monthly_pd.round(2)
print(len(monthly_pd), "months, all equal:", same.all())

# %% 5.7 SQLAlchemy and other databases
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///data/chinook.sqlite")
with engine.connect() as conn:
    genres = pd.read_sql(text("SELECT * FROM Genre"), conn)
print(len(genres), genres["Name"].head(3).tolist())

# %% 5.7 SQLAlchemy and other databases
summary = pd.read_sql_query(
    "SELECT BillingCountry AS country, SUM(Total) AS revenue "
    "FROM Invoice GROUP BY BillingCountry", con)
out = create_engine("sqlite:///reports.sqlite")
summary.to_sql("country_revenue", out, if_exists="replace",
               index=False)
check = pd.read_sql("SELECT COUNT(*) AS n FROM country_revenue", out)
print(check)

# %% 5.8 Query parameters
country = "Brazil"
query = """
SELECT FirstName, LastName, City FROM Customer
WHERE Country = ?
ORDER BY LastName
"""
print(pd.read_sql_query(query, con, params=(country,)))

# %% 5.9 Putting it together: top customers
query = """
SELECT c.CustomerId AS id,
       c.FirstName || ' ' || c.LastName AS customer,
       c.Country AS country,
       COUNT(i.InvoiceId) AS purchases,
       ROUND(SUM(i.Total), 2) AS spent,
       MIN(i.InvoiceDate) AS first,
       MAX(i.InvoiceDate) AS last
FROM Customer AS c
JOIN Invoice AS i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId
"""
customers = pd.read_sql_query(query, con,
                              parse_dates=["first", "last"])
print(customers.shape)

# %% 5.9 Putting it together: top customers
top = (customers
       .assign(years=lambda d: ((d["last"] - d["first"]).dt.days
                                / 365.25).round(1),
               per_purchase=lambda d: (d["spent"] / d["purchases"])
               .round(2))
       .nlargest(5, "spent")
       .loc[:, ["customer", "country", "purchases", "spent",
                "per_purchase", "years"]])
print(top.to_string(index=False))
con.close()

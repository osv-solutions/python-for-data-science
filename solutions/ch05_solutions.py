"""Solutions to the Chapter 5 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch05_solutions.py

The explanations are in ch05_solutions.md."""

# %%
# Setup: recreates the context these solutions build on (from the chapter).
import sqlite3
import pandas as pd

con = sqlite3.connect("data/chinook.sqlite")

# %% Exercise 5.1
catalog = "SELECT name FROM sqlite_master WHERE type = 'table'"
names = pd.read_sql_query(catalog, con)["name"]
counts = {name: con.execute(f'SELECT COUNT(*) FROM "{name}"')
          .fetchone()[0] for name in names}
print(pd.Series(counts).sort_values(ascending=False))

# %% Exercise 5.2
query = """
SELECT Name, Milliseconds / 1000.0 AS seconds
FROM Track
WHERE Milliseconds > 60000
ORDER BY Milliseconds
LIMIT 10
"""
print(pd.read_sql_query(query, con).round(1))

# %% Exercise 5.3
query = """
SELECT Country, COUNT(*) AS customers
FROM Customer
GROUP BY Country
HAVING COUNT(*) >= 3
ORDER BY customers DESC
"""
print(pd.read_sql_query(query, con))

# %% Exercise 5.4
query = """
SELECT ar.Name AS artist, COUNT(*) AS albums
FROM Album AS al
JOIN Artist AS ar ON al.ArtistId = ar.ArtistId
GROUP BY ar.ArtistId
ORDER BY albums DESC
LIMIT 5
"""
print(pd.read_sql_query(query, con))

# %% Exercise 5.5
def invoices_for(country, year):
    """Return the invoices of one country in one year."""
    query = """
    SELECT InvoiceId, InvoiceDate, BillingCity, Total
    FROM Invoice
    WHERE BillingCountry = ? AND strftime('%Y', InvoiceDate) = ?
    ORDER BY InvoiceDate
    """
    return pd.read_sql_query(query, con, params=(country, str(year)),
                             parse_dates=["InvoiceDate"])

germany = invoices_for("Germany", 2011)
print(len(germany), round(germany["Total"].sum(), 2))
print(germany.head(3))

# %% Exercise 5.6
by_sql = pd.read_sql_query("""
    SELECT strftime('%Y', InvoiceDate) AS year, SUM(Total) AS revenue
    FROM Invoice GROUP BY year ORDER BY year""", con)
invoices = pd.read_sql_query("SELECT * FROM Invoice", con,
                             parse_dates=["InvoiceDate"])
year = invoices["InvoiceDate"].dt.year
by_pd = invoices.groupby(year)["Total"].sum()
print(by_sql.round(2))
same = by_sql["revenue"].round(2).values == by_pd.round(2).values
print(same.all())

# %% Exercise 5.7
query = """
SELECT g.Name AS genre,
       COUNT(DISTINCT t.TrackId) AS tracks,
       AVG(il.InvoiceLineId IS NULL) AS unsold_share
FROM Track AS t
JOIN Genre AS g ON t.GenreId = g.GenreId
LEFT JOIN InvoiceLine AS il ON t.TrackId = il.TrackId
GROUP BY g.GenreId
HAVING COUNT(DISTINCT t.TrackId) >= 10
ORDER BY unsold_share DESC
LIMIT 5
"""
print(pd.read_sql_query(query, con).round(2))
con.close()

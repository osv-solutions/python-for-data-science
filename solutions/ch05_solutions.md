# Solutions: Chapter 5, Data from SQL Databases

Worked solutions to the exercises at the end of Chapter 5 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch05_solutions.ipynb`](ch05_solutions.ipynb) or the script `ch05_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
import sqlite3
import pandas as pd

con = sqlite3.connect("data/chinook.sqlite")
```

</details>

## Exercise 5.1

*List the Chinook tables with their row counts.*

```python
catalog = "SELECT name FROM sqlite_master WHERE type = 'table'"
names = pd.read_sql_query(catalog, con)["name"]
counts = {name: con.execute(f'SELECT COUNT(*) FROM "{name}"')
          .fetchone()[0] for name in names}
print(pd.Series(counts).sort_values(ascending=False))
```

Output:

```text
PlaylistTrack    8715
Track            3503
InvoiceLine      2240
Invoice           412
Album             347
Artist            275
Customer           59
Genre              25
Playlist           18
Employee            8
MediaType           5
dtype: int64
```

The table names come from the database's own catalog, so building the `COUNT(*)` queries from them with an f-string is safe here; the double quotes around the name are SQL's way of quoting an identifier. `con.execute(...).fetchone()[0]` runs a query directly through `sqlite3` and takes the single number from its single row. `PlaylistTrack` is by far the largest table.

## Exercise 5.2

*Return the ten shortest tracks that are longer than one minute, with their length in seconds.*

```python
query = """
SELECT Name, Milliseconds / 1000.0 AS seconds
FROM Track
WHERE Milliseconds > 60000
ORDER BY Milliseconds
LIMIT 10
"""
print(pd.read_sql_query(query, con).round(1))
```

Output:

```text
                                                Name  seconds
0                               Soldier Side - Intro     63.8
1                                       Happy Trails     65.5
2                                                Arc     65.6
3               L'orfeo, Act 3, Sinfonia (Orchestra)     66.6
4                                        Salutations     69.1
5  Lamentations of Jeremiah, First Set \ Incipit ...     69.2
6                                    Interlude Zumbi     71.6
7                                    They're Red Hot     71.9
8                                       Maria, Maria     72.5
9                         Divirta-Se (Saindo Da Sua)     74.9
```

The filter is on the original column, in milliseconds; the `SELECT` list converts to seconds only for display.

## Exercise 5.3

*Find the number of customers in each country, for countries with at least three customers.*

```python
query = """
SELECT Country, COUNT(*) AS customers
FROM Customer
GROUP BY Country
HAVING COUNT(*) >= 3
ORDER BY customers DESC
"""
print(pd.read_sql_query(query, con))
```

Output:

```text
          Country  customers
0             USA         13
1          Canada          8
2          France          5
3          Brazil          5
4         Germany          4
5  United Kingdom          3
```

`HAVING` filters the groups after counting. The USA has the most customers by far, 13.

## Exercise 5.4

*Find the five artists with the most albums.*

```python
query = """
SELECT ar.Name AS artist, COUNT(*) AS albums
FROM Album AS al
JOIN Artist AS ar ON al.ArtistId = ar.ArtistId
GROUP BY ar.ArtistId
ORDER BY albums DESC
LIMIT 5
"""
print(pd.read_sql_query(query, con))
```

Output:

```text
         artist  albums
0   Iron Maiden      21
1  Led Zeppelin      14
2   Deep Purple      11
3     Metallica      10
4            U2      10
```

Each album row is joined to its artist, then counted per artist. Grouping by the ID rather than the name is the safer habit: two different artists could share a name.

## Exercise 5.5

*Write `invoices_for(country, year)` with placeholders and test it with Germany and 2011.*

```python
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
```

Output:

```text
8 48.57
   InvoiceId InvoiceDate BillingCity  Total
0        193  2011-04-23   Frankfurt  14.91
1        196  2011-05-19   Stuttgart   1.98
2        219  2011-08-21   Stuttgart   3.96
```

Both values are passed with `params`, in the order of the `?` placeholders. `strftime('%Y', ...)` returns the year as text, so the year is passed as a string too. Germany had 8 invoices in 2011, worth $48.57 in total.

## Exercise 5.6

*Compute revenue per year in SQL and in pandas, and check that they match.*

```python
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
```

Output:

```text
   year  revenue
0  2009   449.46
1  2010   481.45
2  2011   469.58
3  2012   477.53
4  2013   450.58
True
```

Both are sorted by year, so their values can be compared position by position after rounding to cents. Revenue was remarkably steady, between about $450 and $480 a year.

## Exercise 5.7

*For each genre, find the share of its tracks that have never been sold, and list the five highest shares.*

```python
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
```

Output:

```text
               genre  tracks  unsold_share
0        Alternative      40          0.65
1  Electronica/Dance      30          0.61
2     Easy Listening      24          0.58
3        Heavy Metal      28          0.57
4    Science Fiction      13          0.57
```

In SQLite, `il.InvoiceLineId IS NULL` is 1 for an unsold track and 0 for a sold one, so its average is the unsold share. One subtlety: a track sold twice appears on two rows after the left join, which slightly pulls the share down; with Chinook's data, few tracks sold more than once, so the effect is small. `HAVING` leaves out genres with fewer than ten tracks, whose shares would be based on too few tracks to compare fairly.

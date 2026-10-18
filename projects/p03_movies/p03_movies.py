"""Project 3 (Beginner): Movie Ratings Explorer

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p03_movies.py

or open the notebook and run the cells in order.
"""

# %% Step 1: Plan and explore the database
import sqlite3

import pandas as pd

con = sqlite3.connect("data/movies.sqlite")

def sql(query, params=()):
    return pd.read_sql_query(query, con, params=params)

print(sql("SELECT name FROM sqlite_master WHERE type = 'table'"))
for table in ["movies", "movie_genres", "ratings"]:
    print(table, sql(f"SELECT COUNT(*) AS n FROM {table}")["n"][0])

# %% Step 1: Plan and explore the database
print(sql("SELECT * FROM movies LIMIT 3"))
print(sql("SELECT * FROM movie_genres WHERE movie_id <= 2"))
print(sql("SELECT * FROM ratings LIMIT 3"))

# %% Step 2: The naive ranking
NAIVE = """
SELECT m.title, m.year, COUNT(*) AS votes,
       ROUND(AVG(r.rating), 2) AS average
FROM ratings AS r JOIN movies AS m ON m.movie_id = r.movie_id
GROUP BY m.movie_id
ORDER BY average DESC
LIMIT 5
"""
print(sql(NAIVE))

# %% Step 2: The naive ranking
stats = sql("""SELECT movie_id, COUNT(*) AS votes,
                      AVG(rating) AS average
               FROM ratings GROUP BY movie_id""")
print(stats["votes"].describe().round(0))
print(f"{(stats['votes'] < 10).sum()} films with fewer than 10 votes")

# %% Step 3: A minimum number of votes
THRESHOLD = """
SELECT m.title, m.year, COUNT(*) AS votes,
       ROUND(AVG(r.rating), 2) AS average
FROM ratings AS r JOIN movies AS m ON m.movie_id = r.movie_id
GROUP BY m.movie_id
HAVING COUNT(*) >= ?
ORDER BY average DESC
LIMIT 5
"""
print(sql(THRESHOLD, (100,)))

# %% Step 4: A weighted rating
site_average = sql("SELECT AVG(rating) AS a FROM ratings")["a"][0]
m = stats["votes"].median()
v, R = stats["votes"], stats["average"]
stats["weighted"] = v / (v + m) * R + m / (v + m) * site_average
print(f"site average {site_average:.2f}, m = {m:.0f} votes")

# %% Step 4: A weighted rating
movies = sql("SELECT * FROM movies")
ranked = stats.merge(movies, on="movie_id").sort_values(
    "weighted", ascending=False)
ranked["rank"] = range(1, len(ranked) + 1)
cols = ["rank", "title", "year", "votes", "average", "weighted"]
print(ranked[cols].head(6).round(2).to_string(index=False))

# %% Step 4: A weighted rating
lone = ranked["average"].idxmax()
print(ranked.loc[[lone], cols].round(2).to_string(index=False))

# %% Step 5: Genres
pairs = sql("SELECT * FROM movie_genres")
genres = pairs.merge(ranked, on="movie_id")
by_genre = genres.groupby("genre").agg(
    films=("movie_id", "count"), votes=("votes", "sum"),
    weighted=("weighted", "mean")).sort_values("weighted")
print(by_genre.round(2))

# %% Step 6: Old films rate higher
ranked["decade"] = ranked["year"] // 10 * 10
by_decade = ranked.groupby("decade").agg(
    films=("movie_id", "count"), average=("average", "mean"),
    weighted=("weighted", "mean"))
print(by_decade.round(2))

# %% Step 7: Divisive films
popular = sql("""SELECT r.movie_id, r.rating FROM ratings AS r
                 WHERE r.movie_id IN (SELECT movie_id FROM ratings
                                      GROUP BY movie_id
                                      HAVING COUNT(*) >= 200)""")
spread = popular.groupby("movie_id")["rating"].std().rename("spread")
divisive = ranked.merge(spread, on="movie_id").nlargest(3, "spread")
print(divisive[["title", "votes", "average", "spread"]].round(2))

# %% Step 7: Divisive films
import matplotlib.pyplot as plt

known = ranked[ranked["votes"] >= 50]
fig, ax = plt.subplots(figsize=(6.4, 3))
ax.scatter(known["runtime_min"], known["average"], s=8, alpha=0.5,
           color="#1d5c8c")
ax.set_xlabel("Runtime (minutes)")
ax.set_ylabel("Average rating")
plt.show()
print(known["runtime_min"].corr(known["average"]).round(2))

# %% Step 8: Save the results
top = ranked[ranked["votes"] >= 10].head(100)
with pd.ExcelWriter("movie_rankings.xlsx") as writer:
    top[cols].round(2).to_excel(writer, sheet_name="Top 100",
                                index=False)
    by_genre.round(2).to_excel(writer, sheet_name="Genres")
    by_decade.round(2).to_excel(writer, sheet_name="Decades")
con.close()
print(len(top), "films in the top list")

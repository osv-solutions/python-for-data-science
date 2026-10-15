"""Chapter 2: NumPy Essentials

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch02_numpy.py

or open the notebook and run the cells in order.
"""

# %% 2.1 Why arrays
temps_f = [68.0, 75.2, 80.6, 86.0, 91.4, 84.2, 77.0]
temps_c = [round((t - 32) * 5 / 9, 1) for t in temps_f]
print(temps_c)

# %% 2.1 Why arrays
import numpy as np

temps_f = np.array([68.0, 75.2, 80.6, 86.0, 91.4, 84.2, 77.0])
temps_c = (temps_f - 32) * 5 / 9
print(temps_c.round(1))

# %% 2.1 Why arrays
import timeit

many_f = np.linspace(-20, 110, 1_000_000)
as_list = many_f.tolist()
t_list = timeit.timeit(lambda: [(t - 32) * 5 / 9 for t in as_list],
                       number=5) / 5
t_array = timeit.timeit(lambda: (many_f - 32) * 5 / 9, number=5) / 5
print(f"list:  {t_list * 1000:7.1f} ms")
print(f"array: {t_array * 1000:7.1f} ms")
print(f"the array is about {t_list / t_array:.0f} times faster")

# %% 2.2 Creating arrays
print(np.arange(5))
print(np.arange(0, 1, 0.25))
print(np.linspace(0, 1, 5))
print(np.zeros(3), np.ones(3), np.full(3, 7))

# %% 2.2 Creating arrays
sales = np.array([[42, 38, 51],
                  [27, 30, 29],
                  [55, 61, 58],
                  [19, 22, 31]])
print(sales.shape, sales.ndim, sales.size)

# %% 2.2 Creating arrays
hours = np.arange(1, 13)
print(hours.reshape(3, 4))
print(hours.reshape(2, -1).shape)

# %% 2.3 Data types
print(sales.dtype, temps_f.dtype)
flags = temps_f > 80
print(flags, flags.dtype)
print(sales.astype(float)[0])

# %% 2.3 Data types
print(np.array([1, 2, 3.5]).dtype)
print(np.array([1, 2, "3"]))

# %% 2.4 Math and aggregation
prices = np.array([4.99, 12.50, 7.25, 3.10])
units = np.array([10, 3, 6, 25])
revenue = prices * units
print(revenue)
print(np.round(np.sqrt(units), 2))
print(revenue.sum(), revenue.mean(), revenue.max())

# %% 2.4 Math and aggregation
print("total:     ", sales.sum())
print("per month: ", sales.sum(axis=0))
print("per store: ", sales.sum(axis=1))
print("best month per store:", sales.argmax(axis=1))

# %% 2.5 Indexing and slicing
print(sales[2, 1])
print(sales[0])
print(sales[:, 2])
print(sales[1:3, :2])

# %% 2.5 Indexing and slicing
first_row = sales[0]
first_row[0] = 999
print(sales[0])
sales[0, 0] = 42
safe = sales[0].copy()
safe[0] = 999
print(sales[0])

# %% 2.6 Boolean masks
temps_c = ((temps_f - 32) * 5 / 9).round(1)
hot = temps_c > 27
print(hot)
print(temps_c[hot])
print("hot days:", hot.sum(), "share:", hot.mean().round(2))

# %% 2.6 Boolean masks
mild = (temps_c >= 20) & (temps_c <= 27)
print(temps_c[mild])
print(np.where(temps_c > 27, "hot", "ok"))
temps_c[temps_c > 30] = 30
print(temps_c)

# %% 2.7 Broadcasting
targets = np.array([50, 50, 55])
share = sales / targets
print(share.round(2))

# %% 2.7 Broadcasting
store_size = np.array([[1.0], [0.6], [1.4], [0.5]])
print((sales / store_size).round(1))

# %% 2.8 Random numbers
rng = np.random.default_rng(42)
print(rng.integers(1, 7, size=10))
print(rng.normal(loc=170, scale=8, size=4).round(1))
print(rng.choice(["heads", "tails"], size=5))

# %% 2.8 Random numbers
rng = np.random.default_rng(7)
rolls = rng.integers(1, 7, size=(100_000, 2))
totals = rolls.sum(axis=1)
print(rolls[:3])
print("share of sevens:", (totals == 7).mean())

# %% 2.9 Putting it together: a year of store sales
rng = np.random.default_rng(2026)
weeks, days = 52, 7
base = rng.normal(loc=4200, scale=350, size=weeks * days)
boost = np.array([1.0, 0.95, 1.0, 1.05, 1.15, 1.45, 1.30])
daily = base.reshape(weeks, days) * boost
print(daily.shape)
print(daily[:2].round(0))

# %% 2.9 Putting it together: a year of store sales
names = np.array(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
per_day = daily.mean(axis=0)
order = np.argsort(per_day)[::-1]
for name, value in zip(names[order], per_day[order]):
    print(f"{name}  {value:8,.0f}")
weekly = daily.sum(axis=1)
print("best week:", weekly.argmax() + 1,
      "worst:", weekly.argmin() + 1)
print(f"weeks over $33,000: {(weekly > 33_000).sum()}")

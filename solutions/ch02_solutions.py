"""Solutions to the Chapter 2 exercises

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch02_solutions.py

The explanations are in ch02_solutions.md."""

# %% Exercise 2.1
import numpy as np

numbers = np.arange(1, 21)
evens = numbers[numbers % 2 == 0]
print(numbers.sum(), numbers.mean())
print(evens ** 2)

# %% Exercise 2.2
km = np.array([5, 10, 21.1, 42.2])
print((km / 1.609).round(2))

# %% Exercise 2.3
sales = np.array([[42, 38, 51], [27, 30, 29],
                  [55, 61, 58], [19, 22, 31]])
print(sales.mean(axis=1).round(1))
print("best store (position):", sales.sum(axis=1).argmax())
print("share above 40:", (sales > 40).mean().round(2))

# %% Exercise 2.4
grid = np.arange(24).reshape(4, 6)
print(grid[:, -1])
print(grid[1:3])
print(grid[grid % 5 == 0])

# %% Exercise 2.5
rng = np.random.default_rng(1)
visits = rng.poisson(30, size=(7, 14))
hours = np.arange(8, 22)
days = np.array(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
by_hour = visits.mean(axis=0)
by_day = visits.sum(axis=1)
print("busiest hour:", hours[by_hour.argmax()], "average",
      by_hour.max().round(1))
print("quietest day:", days[by_day.argmin()], by_day.min())

# %% Exercise 2.6
scores = np.array([[72, 85, 90], [65, 70, 58], [88, 92, 95],
                   [55, 61, 70], [79, 74, 83]])
centered = scores - scores.mean(axis=0)
print(centered.round(1))
print(centered.mean(axis=0).round(10))

# %% Exercise 2.7
rng = np.random.default_rng(6)
rolls = rng.integers(1, 7, size=(10_000, 50))
is_six = rolls == 6
has_six = is_six.any(axis=1)
first = is_six.argmax(axis=1) + 1
print("games without a six in 50 rolls:", (~has_six).sum())
print("average rolls needed:", first[has_six].mean().round(3))

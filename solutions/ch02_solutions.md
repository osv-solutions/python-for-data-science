# Solutions: Chapter 2, NumPy Essentials

Worked solutions to the exercises at the end of Chapter 2 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch02_solutions.ipynb`](ch02_solutions.ipynb) or the script `ch02_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

## Exercise 2.1

*Create the numbers 1 to 20 and print the sum, the mean and the squares of the even numbers only.*

```python
import numpy as np

numbers = np.arange(1, 21)
evens = numbers[numbers % 2 == 0]
print(numbers.sum(), numbers.mean())
print(evens ** 2)
```

Output:

```text
210 10.5
[  4  16  36  64 100 144 196 256 324 400]
```

`np.arange(1, 21)` stops before 21. The mask `numbers % 2 == 0` keeps the even numbers, and `** 2` squares each of them.

## Exercise 2.2

*Convert `[5, 10, 21.1, 42.2]` from kilometers to miles, rounded to two decimals.*

```python
km = np.array([5, 10, 21.1, 42.2])
print((km / 1.609).round(2))
```

Output:

```text
[ 3.11  6.22 13.11 26.23]
```

One division converts all four distances: a 5K, a 10K, a half marathon and a marathon.

## Exercise 2.3

*For the `sales` table, print each store's average month, the store with the highest total, and the share of figures above 40.*

```python
sales = np.array([[42, 38, 51], [27, 30, 29],
                  [55, 61, 58], [19, 22, 31]])
print(sales.mean(axis=1).round(1))
print("best store (position):", sales.sum(axis=1).argmax())
print("share above 40:", (sales > 40).mean().round(2))
```

Output:

```text
[43.7 28.7 58.  24. ]
best store (position): 2
share above 40: 0.42
```

`mean(axis=1)` averages across each row, one result per store. `argmax` of the row totals gives the position of the best store, 2 (the third store), and the mean of the mask `sales > 40` gives the share of the twelve figures above 40.

## Exercise 2.4

*Reshape `np.arange(24)` into 4 by 6, then print the last column, the middle two rows, and the elements divisible by 5.*

```python
grid = np.arange(24).reshape(4, 6)
print(grid[:, -1])
print(grid[1:3])
print(grid[grid % 5 == 0])
```

Output:

```text
[ 5 11 17 23]
[[ 6  7  8  9 10 11]
 [12 13 14 15 16 17]]
[ 0  5 10 15 20]
```

`grid[:, -1]` takes every row and the last column. `grid[1:3]` takes rows 1 and 2, the middle two of four. A mask on a 2D array returns the selected values as a flat 1D array.

## Exercise 2.5

*Simulate a week of hourly gym visits and find the busiest hour on average and the quietest day.*

```python
rng = np.random.default_rng(1)
visits = rng.poisson(30, size=(7, 14))
hours = np.arange(8, 22)
days = np.array(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
by_hour = visits.mean(axis=0)
by_day = visits.sum(axis=1)
print("busiest hour:", hours[by_hour.argmax()], "average",
      by_hour.max().round(1))
print("quietest day:", days[by_day.argmin()], by_day.min())
```

Output:

```text
busiest hour: 10 average 34.3
quietest day: Sun 382
```

The **Poisson distribution** models counts of events, such as visits, around an average rate, here 30 an hour. Averaging down the rows (`axis=0`) gives one value per opening hour; summing across the columns (`axis=1`) gives one total per day. Using the position from `argmax` or `argmin` as an index into `hours` or `days` turns it into a label. With purely random data, the "busiest" hour is only the luckiest one; real gym data would show a pattern.

## Exercise 2.6

*Subtract each subject's mean from the exam scores so that every column averages zero.*

```python
scores = np.array([[72, 85, 90], [65, 70, 58], [88, 92, 95],
                   [55, 61, 70], [79, 74, 83]])
centered = scores - scores.mean(axis=0)
print(centered.round(1))
print(centered.mean(axis=0).round(10))
```

Output:

```text
[[  0.2   8.6  10.8]
 [ -6.8  -6.4 -21.2]
 [ 16.2  15.6  15.8]
 [-16.8 -15.4  -9.2]
 [  7.2  -2.4   3.8]]
[ 0. -0. -0.]
```

`scores.mean(axis=0)` has shape (3,), one mean per subject, and broadcasting subtracts it from every student's row. The check on the second line shows that each column now averages zero (rounded, because floating-point arithmetic can leave tiny remainders such as `-1e-15`, which print as `-0.`).

## Exercise 2.7

*Estimate the average number of die rolls needed to get a six.*

```python
rng = np.random.default_rng(6)
rolls = rng.integers(1, 7, size=(10_000, 50))
is_six = rolls == 6
has_six = is_six.any(axis=1)
first = is_six.argmax(axis=1) + 1
print("games without a six in 50 rolls:", (~has_six).sum())
print("average rolls needed:", first[has_six].mean().round(3))
```

Output:

```text
games without a six in 50 rolls: 4
average rolls needed: 5.979
```

`argmax` on a Boolean row returns the position of the first `True`, so adding 1 gives the number of rolls up to and including the first six. A row with no six at all would also give position 0, which is why we keep only the rows where `any(axis=1)` is true. With 50 rolls per game, a game without a six is rare, about 1 in 9,000, but in 10,000 games a few happen: 4 here. The estimate, 5.979, is very close to the exact answer, 6.

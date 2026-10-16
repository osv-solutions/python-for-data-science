# Solutions: Chapter 14, Grouping, Aggregating and Reshaping

Worked solutions to the exercises at the end of Chapter 14 of *Python for Data Science* by Vamsi Krishna Kandala. Try each exercise on your own first. Run the code yourself with the notebook [`ch14_solutions.ipynb`](ch14_solutions.ipynb) or the script `ch14_solutions.py`.

Numbers that depend on random data or library versions may differ slightly on your computer; the conclusions should not.

<details>
<summary>Setup code: recreates the data and helpers from the chapter (click to show)</summary>

```python
import pandas as pd

orders = pd.read_parquet("data/shop_orders.parquet")
orders = orders[orders["status"] != "cancelled"].copy()
orders["revenue"] = orders["quantity"] * orders["unit_price"]
orders["month"] = orders["order_date"].dt.to_period("M")
gap = pd.read_csv("data/gapminder.csv")
```

</details>

The solutions start from the chapter's `orders` table, without cancelled orders and with `revenue` and `month` columns, and the Gapminder data as `gap`.

## Exercise 14.1

*Using `penguins.csv`, compute the number of birds and the mean body mass per species and sex, as a table with flat columns.*

```python
penguins = pd.read_csv("data/penguins.csv")
table = penguins.groupby(["species", "sex"], as_index=False).agg(
    birds=("body_mass_g", "size"), mass_g=("body_mass_g", "mean"))
print(table.round(0))
```

Output:

```text
     species     sex  birds  mass_g
0     Adelie  female     73  3369.0
1     Adelie    male     73  4043.0
2  Chinstrap  female     34  3527.0
3  Chinstrap    male     34  3939.0
4     Gentoo  female     58  4680.0
5     Gentoo    male     61  5485.0
```

`as_index=False` keeps `species` and `sex` as ordinary columns, and named aggregation gives flat names. `"size"` counts rows, including any with a missing mass. The rows with no recorded sex are left out, because `groupby` drops missing keys by default. In every species, males are heavier; Gentoo penguins are the heaviest by far.

## Exercise 14.2

*From the orders, find each customer's total revenue and number of orders, and list the ten best customers.*

```python
best = orders.groupby("customer_id").agg(
    revenue=("revenue", "sum"), orders=("order_id", "count"))
print(best.nlargest(10, "revenue").round(2))
```

Output:

```text
             revenue  orders
customer_id                 
C0007         4544.0       5
C0318         617.05       7
C0105          577.2       6
C0060          576.8       7
C0274          545.0       7
C0187          461.5       8
C0235         458.15       5
C0197          451.3       7
C0132         434.55       5
C0155          425.6       8
```

The café, C0007, is far ahead thanks to its two wholesale orders. Below it, the best customers combine many orders with larger bags, which is why the ranking by revenue differs from a ranking by number of orders.

## Exercise 14.3

*Add a column to the orders with each order's revenue as a share of its customer's total, and find the customers for whom one order is more than half their total.*

```python
total = orders.groupby("customer_id")["revenue"].transform("sum")
orders["share"] = orders["revenue"] / total
big = orders[orders["share"] > 0.5]
print(big["customer_id"].nunique(), "customers")
print(big.nlargest(3, "share")[["customer_id", "revenue", "share"]])
```

Output:

```text
160 customers
   customer_id  revenue  share
17       C0213    41.25    1.0
27       C0161     28.8    1.0
44       C0026     57.6    1.0
```

`transform("sum")` puts each customer's total on every one of their orders, so the division works row by row. For 160 customers, one order is more than half of everything they bought. A share of 1.0 means a customer with a single order. Customers whose one order dominates are worth knowing: they bought once, maybe as a gift, and a follow-up email might bring them back.

## Exercise 14.4

*Make a pivot table of the number of orders by weekday (rows) and bag size (columns), with totals. On which weekday do people buy the most 1-kilogram bags, as a share of that day's orders?*

```python
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday"]
orders["weekday"] = pd.Categorical(
    orders["order_date"].dt.day_name(), categories=days, ordered=True)
counts = orders.pivot_table(index="weekday", columns="bag_size",
                            values="order_id", aggfunc="count",
                            margins=True, observed=True)
print(counts)
share = counts["1kg"] / counts["All"]
print(share.drop("All").idxmax(), f"{share.drop('All').max():.0%}")
```

Output:

```text
bag_size   1kg  250g  500g   All
weekday                         
Monday      32    72    50   154
Tuesday     29    71    48   148
Wednesday   35    71    40   146
Thursday    37    72    44   153
Friday      25    60    58   143
Saturday    40    61    52   153
Sunday      39    75    49   163
All        237   482   341  1060
Saturday 26%
```

An ordered categorical keeps the weekdays in calendar order instead of alphabetical. `aggfunc="count"` on `order_id` counts orders, and `margins=True` adds the `All` row and column. Dividing the 1-kilogram column by the totals gives each day's share. Saturday has the highest share, 26%, and Friday the lowest, 17%. With about 150 orders per weekday, a difference of this size could still be chance; Chapter 20 shows how to test it.

## Exercise 14.5

*From Gapminder, compute the population-weighted mean life expectancy per continent and year, and pivot it to one row per continent and one column per year.*

```python
gap["weighted"] = gap["lifeExp"] * gap["pop"]
sums = gap.groupby(["continent", "year"])[["weighted", "pop"]].sum()
sums["lifeExp"] = sums["weighted"] / sums["pop"]
wide = sums["lifeExp"].unstack("year")
print(wide[[1952, 1982, 2007]].round(1))
```

Output:

```text
year       1952  1982  2007
continent                  
Africa     38.8  51.0  54.6
Americas   60.2  69.2  75.4
Asia       42.9  61.6  69.4
Europe     64.9  72.6  77.9
Oceania    69.2  74.6  81.1
```

A weighted mean is the sum of value times weight divided by the sum of weights; summing both parts per group and dividing gives it in two lines. `unstack("year")` moves the `year` level of the index to the columns, the same reshape as `pivot`. Weighting by population changes the picture: Asia's average, dominated by China and India, rose by more than 26 years between 1952 and 2007, the largest gain of any continent.

## Exercise 14.6

*For each country in Gapminder, compute the growth of GDP per capita from 1952 to 2007 as a factor, and the rank of each country within its continent by that growth.*

```python
ends = gap[gap["year"].isin([1952, 2007])].pivot(
    index=["continent", "country"], columns="year", values="gdpPercap")
ends["growth"] = ends[2007] / ends[1952]
ends["rank"] = (ends.groupby("continent")["growth"]
                .rank(ascending=False).astype(int))
print(ends[ends["rank"] == 1].round(1))
```

Output:

```text
year                            1952     2007  growth  rank
continent country                                          
Africa    Equatorial Guinea    375.6  12154.1    32.4     1
Americas  Puerto Rico         3082.0  19328.7     6.3     1
Asia      Taiwan              1206.9  28718.3    23.8     1
Europe    Ireland             5210.3  40676.0     7.8     1
Oceania   Australia          10039.6  34435.4     3.4     1
```

Pivoting the two years side by side, with continent and country as a two-level index, makes the growth one division. Ranking within each continent and keeping rank 1 gives each continent's fastest grower. Equatorial Guinea, with its oil, grew more than 30-fold and Taiwan almost 24-fold, while Australia, already rich in 1952, grew 3.4-fold.

## Exercise 14.7

*Build a table of weekly revenue per region from `store_sales.xlsx`, its 4-week rolling mean, and, for each week, which region was first. Then melt the weekly table into long form.*

```python
sales = pd.read_excel("data/store_sales.xlsx", sheet_name="Orders",
                      header=2)
sales["revenue"] = sales["units"] * sales["unit_price"]
sales["week"] = sales["order_date"].dt.to_period("W").dt.start_time
weekly = sales.pivot_table(index="week", columns="region",
                           values="revenue", aggfunc="sum",
                           fill_value=0)
smooth = weekly.rolling(4).mean()
print(weekly.idxmax(axis=1).value_counts())
long = weekly.reset_index().melt(id_vars="week", var_name="region",
                                 value_name="revenue")
print(long.shape)
print(smooth.dropna().round(0).head(3))
```

Output:

```text
North    5
East     4
South    4
West     1
Name: count, dtype: int64
(56, 3)
region        East   North   South    West
week                                      
2026-01-19  4414.0  2148.0  2054.0  1148.0
2026-01-26  4704.0  3565.0  2052.0  1364.0
2026-02-02  3821.0  3575.0  2292.0   691.0
```

`dt.start_time` turns each weekly period into the date of its Monday, a convenient label. The pivot table gives one row per week and one column per region, with 0 where a region sold nothing that week. `rolling(4).mean()` works on every column at once. `idxmax(axis=1)` returns, for each row, the column with the largest value: the leading region of each week. North led in 5 weeks, East and South in 4 each. Finally, `melt` turns the four region columns into rows, 14 weeks times 4 regions, the long shape that charting libraries expect.

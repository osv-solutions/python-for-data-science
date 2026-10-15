"""Project 1 (Beginner): Personal Spending Analyzer

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p01_spending.py

or open the notebook and run the cells in order.
"""

# %% Step 2: Load and check the data
import pandas as pd

tx = pd.read_csv("data/transactions.csv", parse_dates=["date"])
print(tx.shape)
print(tx.dtypes)
print(tx["date"].min().date(), "to", tx["date"].max().date())
print("missing values:", tx.isna().sum().sum())

# %% Step 2: Load and check the data
print(tx["category"].value_counts().head(5))
print(f"net change: ${tx['amount'].sum():,.2f}")

# %% Step 3: Separate income and spending
income = tx[tx["amount"] > 0]
spending = tx[tx["amount"] < 0].assign(amount=lambda d: -d["amount"])
print(f"income:   ${income['amount'].sum():>10,.2f}"
      f"  ({len(income)} payments)")
print(f"spending: ${spending['amount'].sum():>10,.2f}"
      f"  ({len(spending)} payments)")

# %% Step 4: Month by month
tx["month"] = tx["date"].dt.to_period("M")
by_month = tx.groupby("month")["amount"]
monthly = pd.DataFrame({
    "income": by_month.apply(lambda a: a[a > 0].sum()),
    "spending": by_month.apply(lambda a: -a[a < 0].sum()),
})
monthly["saved"] = monthly["income"] - monthly["spending"]
monthly["rate_%"] = (monthly["saved"] / monthly["income"] * 100)
print(monthly.round(1))

# %% Step 5: Where the money goes
by_cat = (spending.groupby("category")["amount"]
          .agg(["sum", "count"])
          .sort_values("sum", ascending=False))
by_cat["share_%"] = (by_cat["sum"] / by_cat["sum"].sum() * 100)
by_cat["per_month"] = by_cat["sum"] / 6
print(by_cat.round(1))

# %% Step 5: Where the money goes
import matplotlib.pyplot as plt

ax = (by_cat["per_month"].sort_values()
      .plot.barh(color="#1d5c8c", figsize=(6, 3.4)))
ax.set_xlabel("Average spending per month ($)")
ax.set_ylabel("")
ax.set_title("Where the money goes, January to June")
plt.savefig("spending_by_category.png")
plt.show()

# %% Step 6: Big purchases and frequent merchants
not_rent = spending[spending["category"] != "Housing"]
cols = ["date", "description", "category", "amount"]
print(not_rent.nlargest(5, "amount")[cols].to_string(index=False))

# %% Step 6: Big purchases and frequent merchants
merchants = (spending.groupby("description")["amount"]
             .agg(visits="count", total="sum", average="mean")
             .sort_values("visits", ascending=False)
             .head(5))
print(merchants.round(2))

# %% Step 7: Find the recurring bills
spending = spending.assign(month=spending["date"].dt.to_period("M"))
pattern = spending.groupby("description").agg(
    months=("month", "nunique"),
    payments=("amount", "size"),
    amounts=("amount", "nunique"),
    amount=("amount", "first"),
)
bills = pattern[(pattern["months"] == 6) & (pattern["payments"] == 6)]
print(bills.sort_values("amount", ascending=False))

# %% Step 7: Find the recurring bills
fixed = bills[bills["amounts"] == 1].copy()
fixed["per_year"] = fixed["amount"] * 12
services = fixed.drop("OAKWOOD APTS RENT")
print(services[["amount", "per_year"]])
print(f"services: ${services['per_year'].sum():,.2f} a year")

# %% Step 8: Save the report
with pd.ExcelWriter("spending_report.xlsx") as writer:
    monthly.round(2).to_excel(writer, sheet_name="Monthly")
    by_cat.round(2).to_excel(writer, sheet_name="Categories")
    merchants.round(2).to_excel(writer, sheet_name="Merchants")
    fixed.to_excel(writer, sheet_name="Recurring")
book = pd.read_excel("spending_report.xlsx", sheet_name=None)
for name, sheet in book.items():
    print(f"{name:<11}{sheet.shape}")

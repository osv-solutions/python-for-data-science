"""Project 11 (Advanced): A/B Test Analysis

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python p11_abtest.py

or open the notebook and run the cells in order.
"""

# %% Step 1: The plan, written before the data
import textwrap

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

h = proportion_effectsize(0.044, 0.040)
need = NormalIndPower().solve_power(effect_size=h, alpha=0.05,
                                    power=0.8)
print(f"{need:,.0f} visitors per group")

# %% Step 2: Load and audit the export
raw = pd.read_csv("data/ab_signup.csv", parse_dates=["first_visit"])
print(raw.shape)
print(raw.head(3).to_string(index=False))
print(raw["group"].value_counts())

# %% Step 2: Load and audit the export
print(raw.duplicated().sum(), "duplicate rows")
unique = raw.drop_duplicates()
groups = unique.groupby("visitor_id")["group"].nunique()
print((groups > 1).sum(), "visitors in both groups")
print(raw["visitor_id"].str.replace(r"\d", "", regex=True)
      .value_counts())

# %% Step 2: Load and audit the export
clean = raw.drop_duplicates()
clean = clean[~clean["visitor_id"].isin(groups[groups > 1].index)]
clean = clean[~clean["visitor_id"].str.startswith("qa-")]
print(len(raw), "->", len(clean), "visitors")
print(clean["visitor_id"].is_unique)

# %% Step 3: The sample ratio check
def srm_check(df):
    counts = df["group"].value_counts()
    expected = [len(df) / 2] * 2
    p = stats.chisquare(counts, expected).pvalue
    c, n = counts["control"], counts["new_page"]
    return f"{c:,} vs {n:,}, p = {p:.2g}"

print("raw:  ", srm_check(unique))
print("clean:", srm_check(clean))

# %% Step 4: The primary result
summary = clean.groupby("group").agg(
    visitors=("visitor_id", "count"), signups=("signed_up", "sum"))
summary["rate"] = summary["signups"] / summary["visitors"]
print(summary)
table = pd.crosstab(clean["group"], clean["signed_up"])
print(f"p = {stats.chi2_contingency(table).pvalue:.5f}")

# %% Step 4: The primary result
n0, n1 = summary["visitors"]
p0, p1 = summary["rate"]
diff = p1 - p0
se = np.sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
low_d, high_d = (diff - 1.96 * se) * 100, (diff + 1.96 * se) * 100
print(f"+{diff * 100:.2f} points, 95% CI {low_d:.2f} to {high_d:.2f}")

# %% Step 4: The primary result
rng = np.random.default_rng(8)
boot0 = rng.binomial(n0, p0, 10_000) / n0
boot1 = rng.binomial(n1, p1, 10_000) / n1
low, high = np.percentile(boot1 / boot0 - 1, [2.5, 97.5])
print(f"relative lift {p1 / p0 - 1:.1%}, "
      f"95% CI {low:.1%} to {high:.1%}")

# %% Step 5: The guardrail
signups = clean[clean["signed_up"] == 1]
quality = pd.DataFrame({
    "per visitor": clean.groupby("group")["activated"].mean(),
    "per sign-up": signups.groupby("group")["activated"].mean()})
print(quality.round(4))
quality_table = pd.crosstab(signups["group"], signups["activated"])
print(f"p = {stats.chi2_contingency(quality_table).pvalue:.3f}")

# %% Step 6: Effects over time
clean["week"] = (clean["first_visit"] - pd.Timestamp("2025-09-01")
                 ).dt.days // 7 + 1

def lift(df):
    r = df.groupby("group")["signed_up"].agg(["mean", "count"])
    p0, p1 = r["mean"]
    se = np.sqrt((r["mean"] * (1 - r["mean"]) / r["count"]).sum())
    d = p1 - p0
    return pd.Series({"lift": d / p0, "low": (d - 1.96 * se) / p0,
                      "high": (d + 1.96 * se) / p0})

weekly = clean.groupby("week").apply(lift)
print(weekly.round(3))

# %% Step 6: Effects over time
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6.4, 2.8))
ax.errorbar(weekly.index, weekly["lift"] * 100,
            yerr=[(weekly["lift"] - weekly["low"]) * 100,
                  (weekly["high"] - weekly["lift"]) * 100],
            fmt="o", color="#1d5c8c", capsize=4)
ax.axhline(0, color="#888888", lw=0.8)
ax.axhline((p1 / p0 - 1) * 100, color="#c0582b", ls="--", lw=1,
           label="four-week average")
ax.set_xticks([1, 2, 3, 4], [f"Week {w}" for w in range(1, 5)])
ax.set_ylabel("Lift in sign-up rate (%)")
ax.legend(frameon=False)
plt.show()

# %% Step 7: Segments
rows = []
for col in ["device", "source"]:
    for value, part in clean.groupby(col):
        p = stats.chi2_contingency(pd.crosstab(
            part["group"], part["signed_up"])).pvalue
        rates = part.groupby("group")["signed_up"].mean()
        rows.append({"segment": f"{col}={value}",
                     "visitors": len(part),
                     "lift": rates["new_page"] / rates["control"] - 1,
                     "p": p})
segments = pd.DataFrame(rows).set_index("segment")
segments["significant"] = segments["p"] < 0.05 / len(segments)
print(segments.round(4))

# %% Step 8: The decision memo
memo = (
    f"The new sign-up page raised the sign-up rate from {p0:.2%} to "
    f"{p1:.2%} ({p1 / p0 - 1:+.0%}, 95% CI {low:+.0%} to "
    f"{high:+.0%}; p < 0.001) over four weeks with {len(clean):,} "
    f"visitors. "
    f"The lift fell from {weekly['lift'].iloc[0]:.0%} in week 1 to "
    f"{weekly['lift'].iloc[-1]:.0%} in week 4, so the lasting effect "
    f"is likely smaller. Activations per visitor rose "
    f"({quality.iloc[0, 0]:.2%} to {quality.iloc[1, 0]:.2%}), but "
    f"fewer sign-ups may activate ({quality.iloc[0, 1]:.0%} to "
    f"{quality.iloc[1, 1]:.0%}). The gain is concentrated on mobile.")
print(textwrap.fill(memo, 72))

# %% Step 8: The decision memo
results = pd.concat({"sign-up rate": summary["rate"],
                     "activation": quality["per sign-up"]})
results.to_csv("signup_test_results.csv")
weekly.to_csv("signup_test_weekly.csv")
segments.to_csv("signup_test_segments.csv")
print(pd.read_csv("signup_test_segments.csv").shape)

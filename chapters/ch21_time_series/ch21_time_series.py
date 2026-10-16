"""Chapter 21: Time Series Analysis

Companion code for "Python for Data Science"
by Vamsi Krishna Kandala. Run it from this folder:

    python ch21_time_series.py

or open the notebook and run the cells in order.
"""

# %% 21.1 A date index
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

bikes = pd.read_csv("data/bike_daily.csv", parse_dates=["date"],
                    index_col="date")
print(bikes.shape)
print(bikes.head(3))
print(bikes.index.min().date(), "to", bikes.index.max().date())

# %% 21.1 A date index
daily = bikes.asfreq("D")
missing = daily[daily["rides"].isna()].index
print(len(missing), "missing days:", missing[0].date(), "to",
      missing[-1].date())
print(daily.loc["2024-02-10":"2024-02-20", "rides"].to_string())

# %% 21.1 A date index
daily["rides"] = daily["rides"].interpolate(method="time")
daily["holiday"] = daily["holiday"].astype("boolean").fillna(False)
print(daily.loc["2024-02-11":"2024-02-19", "rides"].round(0).tolist())

# %% 21.2 Resampling: changing the frequency
weekly = daily["rides"].resample("W").sum()
monthly = daily["rides"].resample("MS").mean()
yearly = daily["rides"].resample("YS").sum()
print(weekly.head(3).astype(int))
print((yearly / 1e3).round(0).astype(int))

# %% 21.2 Resampling: changing the frequency
import matplotlib.dates as mdates

fig, ax = plt.subplots(figsize=(6.6, 3))
ax.plot(daily.index, daily["rides"], lw=0.4, color="#9cc9d4",
        label="daily")
ax.plot(monthly.index + pd.Timedelta(days=14), monthly, lw=2,
        color="#1d5c8c", label="monthly mean")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_ylabel("Rides per day")
ax.legend(loc="upper left")
plt.show()

# %% 21.3 Rolling windows
smooth = pd.DataFrame({
    "7-day": daily["rides"].rolling(7).mean(),
    "28-day": daily["rides"].rolling(28, center=True).mean(),
})
print(smooth.loc["2025-07-01":"2025-07-05"].round(0))

# %% 21.4 Trend and seasonality
season = daily.groupby(daily.index.month)["rides"].mean()
weekday = daily.groupby(daily.index.dayofweek)["rides"].mean()
growth = yearly.pct_change().dropna()
print((season / season.mean()).round(2).to_frame("month").T)
print((weekday / weekday.mean()).round(2).tolist())
print("growth per year:", (growth * 100).round(1).tolist())

# %% 21.4 Trend and seasonality
from statsmodels.tsa.seasonal import seasonal_decompose

parts = seasonal_decompose(monthly, model="multiplicative", period=12)
fig = parts.plot()
fig.set_size_inches(6.6, 5)
plt.show()

# %% 21.5 Lags and autocorrelation
rides = daily["rides"]
for lag in [1, 7, 30, 365]:
    print(f"lag {lag:>3}: {rides.autocorr(lag):.2f}")
compare = pd.DataFrame({"today": rides, "last week": rides.shift(7)})
print(compare.loc["2025-06-02":"2025-06-04"].round(0))

# %% 21.5 Lags and autocorrelation
level = rides / smooth["28-day"]
wet = pd.cut(daily["precip_mm"], [-0.1, 0, 5, 100],
             labels=["dry", "light rain", "heavy rain"])
print(level.groupby(wet, observed=True).agg(["mean", "count"])
      .round(2))

# %% 21.6 Forecasting: baselines first
train = daily.loc[:"2025-09-30"]
test = daily.loc["2025-10-01":]
actual = test["rides"]
forecasts = {
    "last value": pd.Series(train["rides"].iloc[-1], actual.index),
    "same day last week": rides.shift(7).loc[actual.index],
    "last 28-day mean": pd.Series(train["rides"].iloc[-28:].mean(),
                                  actual.index),
}
print(len(train), "training days,", len(test), "test days")

# %% 21.6 Forecasting: baselines first
def errors(forecast):
    e = actual - forecast
    return {"MAE": e.abs().mean(),
            "MAPE %": (e / actual).abs().mean() * 100}


scores = pd.DataFrame({name: errors(f) for name, f in
                       forecasts.items()}).T
print(scores.round(1))

# %% 21.6 Forecasting: baselines first
last_year = rides.shift(364).loc[actual.index]
growth = (train["rides"].iloc[-365:].sum()
          / train["rides"].iloc[-730:-365].sum())
forecasts["last year x growth"] = last_year * growth
scores = pd.DataFrame({name: errors(f) for name, f in
                       forecasts.items()}).T
print(f"growth factor {growth:.3f}")
print(scores.round(1).sort_values("MAE"))

# %% 21.6 Forecasting: baselines first
from sklearn.linear_model import LinearRegression


def features(df):
    X = pd.DataFrame({"t": (df.index - daily.index[0]).days,
                      "temp": df["temp_max_c"],
                      "rain": np.log1p(df["precip_mm"]),
                      "holiday": df["holiday"].astype(int)},
                     index=df.index)
    dow = pd.get_dummies(df.index.dayofweek, prefix="dow", dtype=int)
    return X.join(dow.set_index(df.index))

# %% 21.6 Forecasting: baselines first
fit_on = train.dropna(subset=["temp_max_c"])
model = LinearRegression().fit(features(fit_on),
                               np.log(fit_on["rides"]))
forecasts["regression"] = pd.Series(
    np.exp(model.predict(features(test))), actual.index)
print(pd.Series(errors(forecasts["regression"])).round(1).to_dict())

# %% 21.7 Putting it together: the fall forecast
fig, ax = plt.subplots(figsize=(6.6, 3.2))
ax.plot(actual.index, actual, color="#1c1f24", lw=1, label="actual")
ax.plot(actual.index, forecasts["last year x growth"], lw=1, ls="--",
        color="#2a9bb0", label="last year x growth")
ax.plot(actual.index, forecasts["regression"], lw=1.2,
        color="#c0582b", label="regression with weather")
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_ylabel("Rides per day")
ax.legend(fontsize=8)
ax.set_title("October to December 2025: forecasts and actual")
plt.show()

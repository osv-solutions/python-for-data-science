"""Hilltop Coffee Roasters sales dashboard (Chapter 23).
Run it with:  streamlit run dashboard.py"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Hilltop sales", layout="wide")


@st.cache_data
def load_orders():
    orders = pd.read_parquet("data/shop_orders.parquet")
    orders = orders[orders["status"] != "cancelled"]
    return orders.assign(
        revenue=orders["quantity"] * orders["unit_price"],
        month=orders["order_date"].dt.to_period("M").dt.start_time)


orders = load_orders()
st.title("Hilltop Coffee Roasters: sales, January to June 2026")

products = sorted(orders["product"].unique())
chosen = st.sidebar.multiselect("Products", products,
                                default=products)
states = st.sidebar.multiselect("States", sorted(
    orders["state"].dropna().unique()))
view = orders[orders["product"].isin(chosen)]
if states:
    view = view[view["state"].isin(states)]

left, middle, right = st.columns(3)
left.metric("Revenue", f"${view['revenue'].sum():,.0f}")
middle.metric("Orders", f"{len(view):,}")
right.metric("Average rating", f"{view['rating'].mean():.2f}")

monthly = view.groupby(["month", "product"])["revenue"].sum()
st.subheader("Revenue per month")
st.line_chart(monthly.unstack("product"))
st.subheader("Slow deliveries cost stars")
stars = view.groupby("shipping_days")["rating"].mean()
st.bar_chart(stars)
with st.expander("Orders"):
    st.dataframe(view[["order_id", "order_date", "product", "state",
                       "quantity", "revenue"]], hide_index=True)

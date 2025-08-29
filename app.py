"""
Personal Spending — Streamlit built-in charts version
- Upload CSV
- Strong KPIs and practical insights
- Built-in charts only (st.line_chart / st.bar_chart / st.area_chart)
"""
#TODO: review charts 

from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np

from utils import preprocess_df

st.set_page_config(page_title="Personal Spending — Built-in", layout="wide")
st.title("💳 Personal Spending — Built-in Charts")
st.caption("Fast, reliable visuals with Streamlit built-ins. Upload CSV → Filter → Insights.")

# ---------------- Sidebar ----------------
uploaded = st.file_uploader("Upload transactions CSV", type=["csv"])
with st.sidebar:
    st.header("Controls")
    include_refunds = st.toggle("Include refunds (credits)?", value=True)
    monthly_budget = st.number_input("Monthly budget (£)", min_value=0.0, value=1000.0, step=50.0)
    st.markdown("---")
    st.write("Filters")
    search_text = st.text_input("Search merchant/description", "")
    debug = st.toggle("Debug mode", value=False)

if not uploaded:
    st.info("Upload your CSV. Expected columns: "
            "`Date/Time of transaction`, `Description`, `Amount (GBP)`, "
            "`Amount (in Charged Currency)`, `Currency`, `Category`, "
            "`Debit or Credit`, `Country`.")
    st.stop()

# ---------------- Load & prepare ----------------
try:
    raw = pd.read_csv(uploaded)
    df = preprocess_df(raw)
except Exception as e:
    st.error(f"Error reading/preprocessing CSV: {e}")
    st.stop()

# Refund filter
f = df.copy()
if not include_refunds:
    f = f[f["signed_amount"] > 0].copy()

if f.empty:
    st.warning("No rows after applying the refunds filter.")
    st.stop()

# Global filters (date & category)
min_date, max_date = f["date"].min(), f["date"].max()
col1, col2 = st.columns(2)
with col1:
    date_range = st.date_input(
        "Date range",
        value=(min_date.to_pydatetime().date(), max_date.to_pydatetime().date()),
        min_value=min_date.to_pydatetime().date(),
        max_value=max_date.to_pydatetime().date(),
    )
with col2:
    all_cats = sorted(f["category"].dropna().astype(str).unique().tolist())
    selected_cats = st.multiselect("Categories", options=all_cats, default=all_cats)

mask = (
    (f["date"] >= pd.to_datetime(date_range[0])) &
    (f["date"] <= pd.to_datetime(date_range[1])) &
    (f["category"].astype(str).isin(selected_cats)) &
    (f["merchant"].str.contains(search_text, case=False, na=False))
)
f = f.loc[mask].copy()

if f.empty:
    st.warning("No transactions match your filters.")
    st.stop()

# ---------------- KPIs ----------------
# Totals
total_spend = float(f["signed_amount"].sum())
txn_count = int(len(f))
avg_txn = float(f["signed_amount"].mean()) if txn_count else 0.0

# Day-level stats
by_day = (
    f.groupby("date", as_index=False)["signed_amount"]
     .sum()
     .rename(columns={"signed_amount": "daily_spend"})
     .sort_values("date")
)
avg_per_day = float(by_day["daily_spend"].mean()) if not by_day.empty else 0.0

# Monthly stats & budget variance
by_month = (
    f.groupby("month", as_index=False)["signed_amount"]
     .sum()
     .rename(columns={"signed_amount": "monthly_spend"})
     .sort_values("month")
)
avg_monthly_spend = float(by_month["monthly_spend"].mean()) if not by_month.empty else 0.0
budget_variance = monthly_budget - avg_monthly_spend

# Work lunch stats
wl = f[f["work_lunch"]]
wl_spend = float(wl["signed_amount"].sum())
wl_count = int(len(wl))
wl_share = (wl_spend / total_spend) if total_spend else 0.0

# Merchant concentration (Herfindahl index)
share = f.groupby("merchant")["signed_amount"].sum()
hhi = float(((share / share.sum()) ** 2).sum()) if share.sum() != 0 else 0.0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Spend", f"£{total_spend:,.2f}")
k2.metric("Transactions", f"{txn_count:,}")
k3.metric("Avg / Txn", f"£{avg_txn:,.2f}")
k4.metric("Avg / Day", f"£{avg_per_day:,.2f}")
k5.metric("Work-Lunch", f"£{wl_spend:,.2f}", f"{wl_count} txns • {wl_share*100:,.1f}%")
k6.metric("Merchant Concentration (HHI)", f"{hhi:.3f}")

st.caption(
    f"Avg monthly spend in selection: **£{avg_monthly_spend:,.2f}** "
    f"(budget **£{monthly_budget:,.0f}**, variance **£{budget_variance:,.2f}**)"
)
st.divider()

# ---------------- Charts (built-in) ----------------
# Daily spend line
st.subheader("📈 Daily Spend")
if by_day.empty:
    st.info("No daily data.")
else:
    st.line_chart(by_day.set_index("date")["daily_spend"])

# Monthly spend bar
st.subheader("📅 Monthly Spend")
if by_month.empty:
    st.info("No monthly data.")
else:
    st.bar_chart(by_month.set_index("month")["monthly_spend"])

# Category spend (bar)
st.subheader("🍱 Spend by Category")
by_cat = (
    f.groupby("category", as_index=False)["signed_amount"]
     .sum()
     .rename(columns={"signed_amount": "category_spend"})
     .sort_values("category_spend", ascending=True)
)
if by_cat.empty:
    st.info("No category data.")
else:
    st.bar_chart(by_cat.set_index("category")["category_spend"])

# Hour-of-day pattern (line)
st.subheader("🕒 Hour-of-Day Spend Pattern")
by_hour = (
    f.groupby("hour", as_index=False)["signed_amount"]
     .sum()
     .rename(columns={"signed_amount": "hour_spend"})
     .sort_values("hour")
)
if by_hour.empty:
    st.info("No hour-of-day data.")
else:
    st.line_chart(by_hour.set_index("hour")["hour_spend"])

# Weekday pattern (bar)
st.subheader("📆 Weekday Spend Pattern")
weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
by_weekday = (
    f.groupby("weekday", as_index=False)["signed_amount"]
     .sum()
     .rename(columns={"signed_amount": "weekday_spend"})
)
# Ensure order
by_weekday["weekday"] = pd.Categorical(by_weekday["weekday"], categories=weekday_order, ordered=True)
by_weekday = by_weekday.sort_values("weekday")
if by_weekday.empty:
    st.info("No weekday data.")
else:
    st.bar_chart(by_weekday.set_index("weekday")["weekday_spend"])

st.divider()

# ---------------- Work-Lunch focus ----------------
st.subheader("🥗 Work-Lunch Focus")
wl_by_month = (
    f.groupby(["month", "work_lunch"], as_index=False)["signed_amount"]
     .sum()
     .pivot(index="month", columns="work_lunch", values="signed_amount")
     .fillna(0.0)
     .rename(columns={True: "Work lunch", False: "Other"})
     .sort_index()
)
if wl_by_month.empty:
    st.info("No work-lunch breakdown available.")
else:
    st.dataframe(wl_by_month, use_container_width=True)
    # Show simple % share table
    denom = wl_by_month.sum(axis=1).replace(0.0, np.nan)
    wl_share_series = (wl_by_month.get("Work lunch", 0.0) / denom).fillna(0.0)
    st.write("Work-lunch share by month:")
    st.line_chart(wl_share_series)

st.divider()

# ---------------- Top merchants & transactions ----------------
c1, c2 = st.columns(2)
with c1:
    st.subheader("🏷️ Top Merchants")
    top_merchants = (
        f.groupby("merchant", as_index=False)["signed_amount"].sum()
         .rename(columns={"signed_amount": "Spend (£)"})
         .sort_values("Spend (£)", ascending=False)
         .head(15)
    )
    st.dataframe(top_merchants, use_container_width=True)

with c2:
    st.subheader("💥 Largest Transactions")
    top_txn = (
        f[["timestamp","merchant","category","signed_amount"]]
         .rename(columns={"signed_amount": "Amount (£)"})
         .sort_values("Amount (£)", ascending=False)
         .head(15)
    )
    st.dataframe(top_txn, use_container_width=True)

# ---------------- Anomaly detection (robust, per-category) ----------------
st.subheader("🔎 Potential Anomalies (per category, MAD rule)")
def mad_outliers(series: pd.Series, k: float = 3.0):
    med = series.median()
    mad = (series - med).abs().median()
    if mad == 0:
        return pd.Series(False, index=series.index)
    return (series - med).abs() > (k * mad)

f_anom = []
for cat, g in f.groupby("category"):
    mask = mad_outliers(g["signed_amount"].abs(), k=3.0)
    if mask.any():
        f_anom.append(g.loc[mask, ["timestamp","merchant","category","signed_amount"]])
anom = pd.concat(f_anom, axis=0) if f_anom else pd.DataFrame(columns=["timestamp","merchant","category","signed_amount"])
if anom.empty:
    st.info("No anomalies detected with the current filters.")
else:
    st.dataframe(
        anom.rename(columns={"signed_amount": "Amount (£)"}).sort_values("Amount (£)", ascending=False),
        use_container_width=True
    )

st.divider()

# ---------------- Downloads ----------------
st.subheader("⬇️ Downloads")
def to_csv_bytes(df_in: pd.DataFrame) -> bytes:
    return df_in.to_csv(index=False).encode("utf-8")

st.download_button("Download filtered transactions (CSV)", data=to_csv_bytes(
    f[["timestamp","merchant","description","category","amount_gbp","signed_amount","currency","country","work_lunch"]]
), file_name="filtered_transactions.csv", mime="text/csv")

st.download_button("Download daily aggregate (CSV)", data=to_csv_bytes(
    by_day.rename(columns={"date":"Date","daily_spend":"Daily Spend (£)"})
), file_name="daily_spend.csv", mime="text/csv")

st.download_button("Download monthly aggregate (CSV)", data=to_csv_bytes(
    by_month.rename(columns={"month":"Month","monthly_spend":"Monthly Spend (£)"})
), file_name="monthly_spend.csv", mime="text/csv")

# ---------------- Debug ----------------
if debug:
    st.divider()
    st.write("Filtered (f) shape:", f.shape)
    st.write("by_day shape:", by_day.shape)
    st.write("by_month shape:", by_month.shape)
    st.write("by_cat sample:")
    st.dataframe(by_cat.head(10))

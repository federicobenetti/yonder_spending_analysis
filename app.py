import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import preprocess_data

st.set_page_config(page_title="Personal Spending Dashboard", layout="wide")

st.title("💳 Personal Spending Dashboard")

uploaded_file = st.file_uploader("Upload your transactions CSV", type="csv")

if uploaded_file:
    df = preprocess_data(uploaded_file)

    st.subheader("📊 Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Spend", f"£{df['Amount (GBP)'].sum():.2f}")
    col2.metric("Transactions", f"{len(df)}")
    col3.metric("Avg per Day", f"£{df.groupby(df['Date/Time of transaction'].dt.date)['Amount (GBP)'].sum().mean():.2f}")

    # Spending by category
    st.subheader("🍽️ Spending by Category")
    category_totals = df.groupby("Category")["Amount (GBP)"].sum().sort_values()
    fig, ax = plt.subplots()
    category_totals.plot(kind="barh", ax=ax)
    st.pyplot(fig)

    # Trend line
    st.subheader("📈 Daily Spending Trend")
    daily_spend = df.groupby(df["Date/Time of transaction"].dt.date)["Amount (GBP)"].sum()
    fig, ax = plt.subplots()
    daily_spend.plot(ax=ax)
    st.pyplot(fig)

    # Work Lunch Spending
    st.subheader("🥗 Work Lunch Spending")
    work_lunch_total = df.loc[df["Work Lunch"], "Amount (GBP)"].sum()
    st.metric("Total Work Lunch Spend", f"£{work_lunch_total:.2f}")

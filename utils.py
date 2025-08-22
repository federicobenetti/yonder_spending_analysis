"""
Utilities for the Streamlit built-in charts version.

Features:
- Standardize column names
- Parse timestamps and amounts
- Signed spend (debits positive; credits negative)
- Normalized datetime date column
- Simple work-lunch flag: weekday + 11:30–14:00 + category == 'Eating Out'
"""

from __future__ import annotations
import pandas as pd
import numpy as np

_LUNCH_START_MIN = 11 * 60 + 30   # 11:30
_LUNCH_END_MIN   = 14 * 60        # 14:00 (exclusive)

EXPECTED_MAP = {
    "Date/Time of transaction": "timestamp",
    "Description": "description",
    "Amount (GBP)": "amount_gbp",
    "Amount (in Charged Currency)": "amount_ccy",
    "Currency": "currency",
    "Category": "category",
    "Debit or Credit": "dr_cr",
    "Country": "country",
}

def _is_work_lunch(ts: pd.Timestamp, category: str) -> bool:
    if pd.isna(ts):
        return False
    is_weekday = ts.weekday() < 5
    mins = ts.hour * 60 + ts.minute
    in_window = (_LUNCH_START_MIN <= mins < _LUNCH_END_MIN)
    return (str(category).strip().lower() == "eating out") and is_weekday and in_window

def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=EXPECTED_MAP)

    missing = [c for c in EXPECTED_MAP.values() if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Parse timestamp (tz-naive)
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=False)
    df = df.dropna(subset=["timestamp"]).copy()
    df["timestamp"] = df["timestamp"].dt.tz_localize(None)

    # Numeric amounts
    df["amount_gbp"] = pd.to_numeric(df["amount_gbp"], errors="coerce").fillna(0.0)

    # Debits positive (spend), Credits negative (refunds)
    drcr = df["dr_cr"].astype(str).str.lower().str.strip()
    df["signed_amount"] = np.where(drcr.str.startswith("debit"), df["amount_gbp"], -df["amount_gbp"])

    # Helpful time fields
    df["date"] = df["timestamp"].dt.normalize()             # datetime64[ns] at midnight
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    df["weekday"] = df["timestamp"].dt.day_name()
    df["hour"] = df["timestamp"].dt.hour

    # Merchant / work-lunch flag
    df["merchant"] = df["description"].astype(str).str.strip()
    df["work_lunch"] = df.apply(lambda r: _is_work_lunch(r["timestamp"], r["category"]), axis=1)

    return df.sort_values("timestamp").reset_index(drop=True)

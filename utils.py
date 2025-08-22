import pandas as pd
import holidays

def preprocess_data(file_path):
    uk_holidays = holidays.UK()

    df = pd.read_csv(file_path, parse_dates=["Date/Time of transaction"])

    # Add day of week
    df["Day of Week"] = df["Date/Time of transaction"].dt.day_name()

    # Add weekend flag
    df["Is Weekend"] = df["Date/Time of transaction"].dt.weekday >= 5

    # Add week number
    df["Week Number"] = df["Date/Time of transaction"].dt.isocalendar().week

    # Add Work Lunch flag
    def is_work_lunch(row):
        ts = row["Date/Time of transaction"]
        is_weekday = ts.weekday() < 5 and ts.date() not in uk_holidays
        is_lunch_time = 11 <= ts.hour < 14
        return row["Category"] == "Eating Out" and is_weekday and is_lunch_time

    df["Work Lunch"] = df.apply(is_work_lunch, axis=1)

    # Cumulative spending
    df = df.sort_values("Date/Time of transaction")
    df["Cumulative Spend"] = df["Amount (GBP)"].cumsum()

    return df

import pandas as pd
from datetime import timedelta


def make_stats(df):

    date_col = None

    for c in df.columns:
        if "date" in c.lower():
            date_col = c
            break

    amount_col = None

    for c in df.columns:
        if c.lower() == "amount":
            amount_col = c
            break

    df = df.copy()

    df[date_col] = pd.to_datetime(df[date_col])

    today = df[date_col].max().normalize()

    stats = {}

    
    periods = {
        "today": 1,
        "week": 7,
        "month": 30,
    }

    for name, days in periods.items():

        start = today - timedelta(days=days - 1)

        d = df[df[date_col] >= start]

        stats[name] = {
            "sales": len(d),
            "revenue": d[amount_col].sum()
        }
        stats["total"] = {
            "sales": len(df),
            "revenue": df[amount_col].sum()
        }

    return stats
"""Pure aggregations and anomaly detection on a normalized hours DataFrame."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd


def compute_week_range(today: date) -> tuple[date, date]:
    """Return (Sunday, Saturday) of the week that ended before `today`.

    Convention: Sunday is day 0 of an Israeli work week.
    Python's weekday(): Mon=0..Sun=6. Adjust accordingly.
    """
    py_weekday = today.weekday()  # Mon=0..Sun=6
    days_since_sunday = (py_weekday + 1) % 7
    most_recent_sunday = today - timedelta(days=days_since_sunday)
    last_week_sunday = most_recent_sunday - timedelta(days=7)
    last_week_saturday = last_week_sunday + timedelta(days=6)
    return last_week_sunday, last_week_saturday


def filter_to_range(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Return rows whose 'date' column falls within [start, end] inclusive."""
    mask = (df["date"] >= start) & (df["date"] <= end)
    return df.loc[mask].copy()


def total_hours_per_employee(df: pd.DataFrame) -> dict[str, timedelta]:
    """Sum 'duration' per employee, ignoring rows with missing duration."""
    valid = df.dropna(subset=["duration"])
    totals: dict[str, timedelta] = {}
    for emp, group in valid.groupby("employee"):
        totals[emp] = group["duration"].sum() if len(group) else timedelta(0)
    return totals


def hours_per_client_per_employee(df: pd.DataFrame) -> dict[str, dict[str, timedelta]]:
    """Sum hours per (employee, client). Returns nested dict {emp: {client: hours}}."""
    valid = df.dropna(subset=["duration"])
    result: dict[str, dict[str, timedelta]] = {}
    for (emp, client), group in valid.groupby(["employee", "client"]):
        if not client:
            continue
        result.setdefault(emp, {})[client] = group["duration"].sum()
    return result


def top_tasks_by_duration(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    """Return the top `limit` task rows by duration descending."""
    valid = df.dropna(subset=["duration"])
    if valid.empty:
        return []
    sorted_df = valid.sort_values("duration", ascending=False).head(limit)
    return [
        {
            "employee": row["employee"],
            "client": row["client"],
            "task": row["task"],
            "date": row["date"],
            "duration": row["duration"],
        }
        for _, row in sorted_df.iterrows()
    ]

"""Pure aggregations and anomaly detection on a normalized hours DataFrame."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
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


def detect_missing_data(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return rows that have a valid date but missing time/duration fields."""
    issues_present = df[df["issues"].apply(lambda lst: bool(lst))]
    return [
        {
            "employee": row["employee"],
            "date": row["date"],
            "task": row["task"],
            "client": row["client"],
            "missing_fields": row["issues"],
        }
        for _, row in issues_present.iterrows()
    ]


_WEEKDAY_NAMES = {
    "sunday": 6, "monday": 0, "tuesday": 1, "wednesday": 2,
    "thursday": 3, "friday": 4, "saturday": 5,
}


def detect_missing_days(
    df: pd.DataFrame,
    start: date,
    end: date,
    workdays: list[str],
    employees: list[str],
) -> list[dict[str, Any]]:
    """Find workdays in [start, end] where an employee has zero entries."""
    workday_indices = {_WEEKDAY_NAMES[d.lower()] for d in workdays}
    result: list[dict[str, Any]] = []
    current = start
    while current <= end:
        if current.weekday() in workday_indices:
            for emp in employees:
                emp_rows = df[(df["employee"] == emp) & (df["date"] == current)]
                if emp_rows.empty:
                    result.append({"employee": emp, "date": current, "note": "אין דיווח כלל ביום זה"})
        current += timedelta(days=1)
    return result


def detect_long_tasks(df: pd.DataFrame, threshold_hours: float) -> list[dict[str, Any]]:
    """Return rows whose single-task duration exceeds threshold_hours."""
    valid = df.dropna(subset=["duration"])
    threshold = timedelta(hours=threshold_hours)
    long_rows = valid[valid["duration"] > threshold]
    return [
        {
            "employee": row["employee"],
            "date": row["date"],
            "client": row["client"],
            "task": row["task"],
            "duration": row["duration"],
        }
        for _, row in long_rows.iterrows()
    ]


def detect_under_over_reporting(
    df: pd.DataFrame,
    under_threshold_hours: float,
    over_threshold_hours: float,
    workdays: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Find (employee, day) pairs where total daily hours fall outside thresholds.

    Only considers workdays (skips weekend days).
    """
    workday_indices = {_WEEKDAY_NAMES[d.lower()] for d in workdays}
    valid = df.dropna(subset=["duration"])
    daily = valid.groupby(["employee", "date"])["duration"].sum().reset_index()
    under: list[dict[str, Any]] = []
    over: list[dict[str, Any]] = []
    under_thresh = timedelta(hours=under_threshold_hours)
    over_thresh = timedelta(hours=over_threshold_hours)
    for _, row in daily.iterrows():
        if row["date"].weekday() not in workday_indices:
            continue
        if row["duration"] < under_thresh:
            under.append({"employee": row["employee"], "date": row["date"], "total": row["duration"]})
        if row["duration"] > over_thresh:
            over.append({"employee": row["employee"], "date": row["date"], "total": row["duration"]})
    return under, over


def detect_schedule_gaps(df: pd.DataFrame, threshold_minutes: int) -> list[dict[str, Any]]:
    """Find intra-day gaps between consecutive tasks longer than threshold_minutes."""
    valid = df.dropna(subset=["from_time", "to_time"]).copy()
    threshold = timedelta(minutes=threshold_minutes)
    gaps: list[dict[str, Any]] = []
    for (emp, day), group in valid.groupby(["employee", "date"]):
        sorted_group = group.sort_values("from_time")
        prev_end: time | None = None
        for _, row in sorted_group.iterrows():
            if prev_end is not None and row["from_time"] > prev_end:
                delta = datetime.combine(day, row["from_time"]) - datetime.combine(day, prev_end)
                if delta > threshold:
                    gaps.append({
                        "employee": emp,
                        "date": day,
                        "gap_start": prev_end,
                        "gap_end": row["from_time"],
                        "duration": delta,
                    })
            prev_end = row["to_time"]
    return gaps

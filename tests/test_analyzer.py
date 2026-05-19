from datetime import date, timedelta

import pandas as pd

from scripts.analyzer import (
    compute_week_range,
    filter_to_range,
    hours_per_client_per_employee,
    top_tasks_by_duration,
    total_hours_per_employee,
)
from scripts.sheets_reader import normalize_workbook


def test_compute_week_range_from_sunday():
    """Cron fires Sunday 2026-04-19. Last week = Sun 04-12 .. Sat 04-18."""
    today = date(2026, 4, 19)
    start, end = compute_week_range(today)
    assert start == date(2026, 4, 12)
    assert end == date(2026, 4, 18)


def test_compute_week_range_from_midweek():
    """If today is Wednesday 04-15, last week is still 04-05 .. 04-11."""
    today = date(2026, 4, 15)
    start, end = compute_week_range(today)
    assert start == date(2026, 4, 5)
    assert end == date(2026, 4, 11)


def test_filter_to_range(sample_sheet_data, default_config, reference_week):
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    start, end = reference_week
    filtered = filter_to_range(df, start, end)
    assert all(start <= d <= end for d in filtered["date"])
    # Should exclude the prev-week rows
    assert date(2026, 4, 5) not in filtered["date"].values


def test_total_hours_per_employee(sample_sheet_data, default_config, reference_week):
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    week_df = filter_to_range(df, *reference_week)
    totals = total_hours_per_employee(week_df)
    # אופיר reference week:
    #   12.04: 00:15+01:40+03:00 = 04:55
    #   13.04: 00:20+04:10+02:00 = 06:30
    #   14.04: duration missing (excluded from sum)
    #   15.04: 01:00+01:00 = 02:00
    #   16.04: 00:30
    # Total: 13:55
    assert totals["אופיר"] == timedelta(hours=13, minutes=55)
    # אביב reference week: 07:00 (12) + 07:00 (13) + 11:00 (14) + 07:00 (16) = 32:00
    assert totals["אביב"] == timedelta(hours=32)


def test_hours_per_client_per_employee(sample_sheet_data, default_config, reference_week):
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    week_df = filter_to_range(df, *reference_week)
    grouped = hours_per_client_per_employee(week_df)
    # אופיר/משרד: 00:15 (12) + 01:40 (12) + 00:20 (13) + 01:00 (15) + 00:30 (16) = 03:45
    assert grouped["אופיר"]["משרד"] == timedelta(hours=3, minutes=45)
    # אופיר/גינדי: 03:00 (12) + 02:00 (13) + 01:00 (15) = 06:00
    assert grouped["אופיר"]["גינדי"] == timedelta(hours=6)
    # אופיר/מעוז דניאל: 04:10 (13)
    assert grouped["אופיר"]["מעוז דניאל"] == timedelta(hours=4, minutes=10)


def test_top_tasks_by_duration(sample_sheet_data, default_config, reference_week):
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    week_df = filter_to_range(df, *reference_week)
    top = top_tasks_by_duration(week_df, limit=3)
    assert len(top) == 3
    # Top single tasks: 11:00 (אביב 14.04), 07:00 (אביב x3 in ref week), 04:10 (אופיר 13.04)
    assert top[0]["duration"] == timedelta(hours=11)
    assert top[0]["employee"] == "אביב"
    assert top[0]["date"] == date(2026, 4, 14)

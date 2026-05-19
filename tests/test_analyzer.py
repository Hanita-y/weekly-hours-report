from datetime import date, time, timedelta

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


from scripts.analyzer import detect_missing_data


def test_detect_missing_data(sample_sheet_data, default_config, reference_week):
    from scripts.sheets_reader import normalize_workbook
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    week_df = filter_to_range(df, *reference_week)
    missing = detect_missing_data(week_df)
    # Exactly one row in the reference week has missing duration: אופיר 14.04
    assert len(missing) == 1
    assert missing[0]["employee"] == "אופיר"
    assert missing[0]["date"] == date(2026, 4, 14)
    assert "duration_missing" in missing[0]["missing_fields"]


from scripts.analyzer import detect_missing_days


def test_detect_missing_days(sample_sheet_data, default_config, reference_week):
    from scripts.sheets_reader import normalize_workbook
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    week_df = filter_to_range(df, *reference_week)
    missing_days = detect_missing_days(
        week_df,
        start=reference_week[0],
        end=reference_week[1],
        workdays=default_config["workdays"],
        employees=default_config["sheet"]["employee_tabs"],
    )
    # אביב has no entry on Wed 15.04
    aviv_misses = [m for m in missing_days if m["employee"] == "אביב"]
    assert any(m["date"] == date(2026, 4, 15) for m in aviv_misses)
    # אופיר reported every workday in the week → no entries
    ofir_misses = [m for m in missing_days if m["employee"] == "אופיר"]
    assert ofir_misses == []


from scripts.analyzer import detect_long_tasks


def test_detect_long_tasks(sample_sheet_data, default_config, reference_week):
    from scripts.sheets_reader import normalize_workbook
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    week_df = filter_to_range(df, *reference_week)
    long_tasks = detect_long_tasks(week_df, threshold_hours=3)
    employees_dates = {(t["employee"], t["date"]) for t in long_tasks}
    assert ("אופיר", date(2026, 4, 13)) in employees_dates
    assert ("אביב", date(2026, 4, 14)) in employees_dates
    # 03:00 is NOT > 3h (strict greater-than)
    assert ("אופיר", date(2026, 4, 12)) not in employees_dates


from scripts.analyzer import detect_under_over_reporting


def test_detect_under_over_reporting(sample_sheet_data, default_config, reference_week):
    from scripts.sheets_reader import normalize_workbook
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    week_df = filter_to_range(df, *reference_week)
    under, over = detect_under_over_reporting(
        week_df,
        under_threshold_hours=6,
        over_threshold_hours=10,
        workdays=default_config["workdays"],
    )
    # אופיר 15.04 total = 02:00 (under)
    # אופיר 16.04 total = 00:30 (under)
    # אביב 14.04 total = 11:00 (over)
    under_pairs = {(u["employee"], u["date"]) for u in under}
    over_pairs = {(o["employee"], o["date"]) for o in over}
    assert ("אופיר", date(2026, 4, 15)) in under_pairs
    assert ("אופיר", date(2026, 4, 16)) in under_pairs
    assert ("אביב", date(2026, 4, 14)) in over_pairs


from scripts.analyzer import detect_schedule_gaps


def test_detect_schedule_gaps():
    # Build a small DataFrame by hand
    df = pd.DataFrame([
        {"employee": "אופיר", "date": date(2026, 4, 12),
         "from_time": time(9, 0), "to_time": time(10, 0),
         "duration": timedelta(hours=1), "issues": []},
        {"employee": "אופיר", "date": date(2026, 4, 12),
         "from_time": time(11, 0), "to_time": time(12, 0),
         "duration": timedelta(hours=1), "issues": []},
        {"employee": "אופיר", "date": date(2026, 4, 12),
         "from_time": time(12, 5), "to_time": time(13, 0),
         "duration": timedelta(minutes=55), "issues": []},
    ])
    gaps = detect_schedule_gaps(df, threshold_minutes=30)
    # Gap 10:00 → 11:00 = 60 minutes > 30 → reported
    # Gap 12:00 → 12:05 = 5 minutes < 30 → not reported
    assert len(gaps) == 1
    assert gaps[0]["gap_start"] == time(10, 0)
    assert gaps[0]["gap_end"] == time(11, 0)


from scripts.analyzer import week_over_week


def test_week_over_week(sample_sheet_data, default_config, reference_week, prev_reference_week):
    from scripts.sheets_reader import normalize_workbook
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    this_week = filter_to_range(df, *reference_week)
    prev_week = filter_to_range(df, *prev_reference_week)
    wow = week_over_week(this_week, prev_week)
    assert wow["this_week"]["total_hours"] > timedelta(0)
    assert wow["prev_week"]["total_hours"] > timedelta(0)
    assert "hours_pct" in wow["delta"]
    assert "per_employee_delta" in wow
    aviv_delta = next(e for e in wow["per_employee_delta"] if e["name"] == "אביב")
    # אביב this week = 32h, prev week = 28h (4 × 7h) → +14.3%
    assert aviv_delta["this"] == timedelta(hours=32)
    assert aviv_delta["prev"] == timedelta(hours=28)


from scripts.analyzer import build_report


def test_build_report_shape(sample_sheet_data, default_config):
    from scripts.sheets_reader import normalize_workbook
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    today = date(2026, 4, 19)  # Sunday after the reference week
    report = build_report(df, today, default_config)
    for key in [
        "date_range", "prev_range", "totals", "per_client", "top_tasks",
        "anomalies", "wow",
    ]:
        assert key in report, f"missing key: {key}"
    assert report["date_range"]["start"] == date(2026, 4, 12)
    assert report["date_range"]["end"] == date(2026, 4, 18)
    assert "missing_data" in report["anomalies"]
    assert "missing_days" in report["anomalies"]
    assert "long_tasks" in report["anomalies"]
    assert "schedule_gaps" in report["anomalies"]
    assert "under_reporting" in report["anomalies"]
    assert "over_reporting" in report["anomalies"]

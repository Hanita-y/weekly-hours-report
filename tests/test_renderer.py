"""Tests for scripts/renderer.py — format helpers, template context, HTML output."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from scripts.renderer import (
    build_template_context,
    delta_class,
    format_date,
    format_duration,
    format_pct,
    render_email_html,
)


# ---------- A. format_duration ----------


def test_format_duration_under_hour():
    assert format_duration(timedelta(minutes=30)) == "00:30"


def test_format_duration_hours_minutes():
    assert format_duration(timedelta(hours=13, minutes=55)) == "13:55"


def test_format_duration_days_overflow():
    assert format_duration(timedelta(hours=184, minutes=30)) == "184:30"


def test_format_duration_zero():
    assert format_duration(timedelta(0)) == "00:00"


# ---------- B. format_date, format_pct, delta_class ----------


def test_format_date():
    assert format_date(date(2026, 4, 12)) == "12.04.26"


def test_format_pct_positive():
    assert format_pct(4.7) == "+4.7%"


def test_format_pct_negative():
    assert format_pct(-2.1) == "-2.1%"


def test_format_pct_none():
    assert format_pct(None) == "—"


def test_delta_class():
    assert delta_class(4.7) == "delta-positive"
    assert delta_class(-2.1) == "delta-negative"
    assert delta_class(0) == "delta-neutral"
    assert delta_class(None) == "delta-neutral"


# ---------- C. build_template_context ----------


def test_build_template_context_shape(sample_sheet_data, default_config):
    from scripts.sheets_reader import normalize_workbook
    from scripts.analyzer import build_report
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    today = date(2026, 4, 19)
    report = build_report(df, today, default_config)
    ctx = build_template_context(report, default_config, generated_at=datetime(2026, 4, 19, 8, 0))
    assert "date_range" in ctx
    assert ctx["date_range"]["start_str"] == "12.04.26"
    assert "tables" in ctx
    assert "per_employee" in ctx["tables"]
    assert "anomaly_lines" in ctx
    assert "css" in ctx
    assert "generated_at" in ctx


# ---------- D. render_email_html ----------


def test_render_email_html(sample_sheet_data, default_config):
    from scripts.sheets_reader import normalize_workbook
    from scripts.analyzer import build_report
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    report = build_report(df, date(2026, 4, 19), default_config)
    html = render_email_html(report, default_config, datetime(2026, 4, 19, 8, 0))
    assert "<!DOCTYPE html>" in html
    assert 'dir="rtl"' in html
    assert "Assistant" in html  # font reference
    assert "דוח שעות שבועי" in html
    assert "אופיר" in html
    assert "אביב" in html
    # Anomalies should appear
    assert "מידע חסר" in html
    assert "פעולות ארוכות" in html

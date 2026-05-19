"""Render the metrics dict into HTML output for the email body."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


# ---------- A. Duration formatter ----------


def format_duration(td: timedelta) -> str:
    """Format a timedelta as HH:MM (hours can exceed 24)."""
    total_seconds = int(td.total_seconds())
    sign = "-" if total_seconds < 0 else ""
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


# ---------- B. Date / percent / delta-class formatters ----------


def format_date(d: date) -> str:
    return d.strftime("%d.%m.%y")


def format_pct(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value}%"


def delta_class(value: float | None) -> str:
    if value is None or value == 0:
        return "delta-neutral"
    return "delta-positive" if value > 0 else "delta-negative"


# ---------- C. Template context builder ----------


def _load_css() -> str:
    return (TEMPLATES_DIR / "styles.css").read_text(encoding="utf-8")


def _per_employee_rows(wow: dict[str, Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for emp in wow["per_employee_delta"]:
        rows.append([
            emp["name"],
            f'<span class="num">{format_duration(emp["this"])}</span>',
            f'<span class="num {delta_class(emp["delta_pct"])}">{format_pct(emp["delta_pct"])}</span>',
        ])
    return rows


def _per_client_rows(per_client: dict[str, dict[str, timedelta]]) -> list[list[str]]:
    client_totals: dict[str, timedelta] = {}
    for emp_clients in per_client.values():
        for client, td in emp_clients.items():
            client_totals[client] = client_totals.get(client, timedelta(0)) + td
    grand_total = sum(client_totals.values(), timedelta(0))
    rows: list[list[str]] = []
    for client, td in sorted(client_totals.items(), key=lambda kv: -kv[1].total_seconds()):
        pct = (td.total_seconds() / grand_total.total_seconds() * 100) if grand_total.total_seconds() else 0
        rows.append([
            client,
            f'<span class="num">{format_duration(td)}</span>',
            f'<span class="num">{pct:.0f}%</span>',
        ])
    return rows


def _anomaly_lines(anomalies: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    def fmt_missing(item: dict[str, Any]) -> str:
        fields = ", ".join(item["missing_fields"])
        return f'{item["employee"]} — <span class="num">{format_date(item["date"])}</span> — חסר: {fields}'

    def fmt_missing_day(item: dict[str, Any]) -> str:
        return f'{item["employee"]} — <span class="num">{format_date(item["date"])}</span>'

    def fmt_long_task(item: dict[str, Any]) -> str:
        return (f'{item["employee"]} — <span class="num">{format_date(item["date"])}</span> — '
                f'{item["task"]} — <span class="num">{format_duration(item["duration"])}</span>')

    def fmt_under(item: dict[str, Any]) -> str:
        return (f'{item["employee"]} — <span class="num">{format_date(item["date"])}</span> — '
                f'<span class="num">{format_duration(item["total"])}</span>')

    def fmt_gap(item: dict[str, Any]) -> str:
        return (f'{item["employee"]} — <span class="num">{format_date(item["date"])}</span> — '
                f'<span class="num">{item["gap_start"].strftime("%H:%M")}</span> '
                f'עד <span class="num">{item["gap_end"].strftime("%H:%M")}</span> '
                f'(<span class="num">{format_duration(item["duration"])}</span>)')

    return {
        "missing_data": [fmt_missing(i) for i in anomalies["missing_data"]],
        "missing_days": [fmt_missing_day(i) for i in anomalies["missing_days"]],
        "long_tasks": [fmt_long_task(i) for i in anomalies["long_tasks"]],
        "under_reporting": [fmt_under(i) for i in anomalies["under_reporting"]],
        "over_reporting": [fmt_under(i) for i in anomalies["over_reporting"]],
        "schedule_gaps": [fmt_gap(i) for i in anomalies["schedule_gaps"]],
    }


def _subject(report: dict[str, Any], config: dict[str, Any]) -> str:
    template = config["email"]["subject_template"]
    start = report["date_range"]["start"]
    end = report["date_range"]["end"]
    months_he = ["", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
                 "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
    if start.month == end.month:
        date_range = f"{start.day}–{end.day} {months_he[start.month]}"
    else:
        date_range = f"{format_date(start)}–{format_date(end)}"
    total = format_duration(report["wow"]["this_week"]["total_hours"])
    return template.format(date_range=date_range, total_hours=total)


def build_template_context(
    report: dict[str, Any],
    config: dict[str, Any],
    generated_at: datetime,
) -> dict[str, Any]:
    """Transform the analyzer's report dict into the dict Jinja templates expect."""
    wow = report["wow"]
    return {
        "subject": _subject(report, config),
        "css": _load_css(),
        "branding": {
            **report.get("branding", {}),
            "footer_text": report.get("branding", {}).get(
                "footer_text", config.get("branding", {}).get("footer_text", "")
            ),
        },
        "date_range": {
            "start": report["date_range"]["start"],
            "end": report["date_range"]["end"],
            "start_str": format_date(report["date_range"]["start"]),
            "end_str": format_date(report["date_range"]["end"]),
        },
        "wow": {
            "this_week": {
                "total_hours_str": format_duration(wow["this_week"]["total_hours"]),
                "total_tasks": wow["this_week"]["total_tasks"],
            },
            "delta": {
                "hours_pct_str": format_pct(wow["delta"]["hours_pct"]),
                "hours_class": delta_class(wow["delta"]["hours_pct"]),
            },
        },
        "tables": {
            "per_employee": _per_employee_rows(wow),
            "per_client": _per_client_rows(report["per_client"]),
        },
        "top_tasks": [
            {
                "task": t["task"],
                "client": t["client"],
                "employee": t["employee"],
                "duration_str": format_duration(t["duration"]),
            }
            for t in report["top_tasks"]
        ],
        "anomaly_lines": _anomaly_lines(report["anomalies"]),
        "generated_at": generated_at.strftime("%d.%m.%Y %H:%M"),
    }


# ---------- D. Renderers ----------


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
    )


def render_email_html(report: dict[str, Any], config: dict[str, Any], generated_at: datetime) -> str:
    ctx = build_template_context(report, config, generated_at)
    return _env().get_template("email.html").render(**ctx)

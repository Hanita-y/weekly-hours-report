"""Reads Google Sheets workbooks and returns a normalized DataFrame."""
from __future__ import annotations

from datetime import date, time, timedelta
from typing import Any

import pandas as pd


def column_letter_to_index(letter: str) -> int:
    """Convert spreadsheet column letter (A, B, ..., Z, AA, ...) to 0-based index."""
    letter = letter.upper()
    result = 0
    for ch in letter:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1


def parse_hebrew_date(value: Any) -> date | None:
    """Parse 'DD.MM.YY' format. Returns None for invalid input."""
    if not value or not isinstance(value, str):
        return None
    try:
        parts = value.strip().split(".")
        if len(parts) != 3:
            return None
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        if year < 100:
            year += 2000
        return date(year, month, day)
    except (ValueError, AttributeError):
        return None


def parse_time(value: Any) -> time | None:
    """Parse 'HH:MM' or 'H:MM' format. Returns None for invalid input."""
    if not value or not isinstance(value, str):
        return None
    try:
        parts = value.strip().split(":")
        if len(parts) != 2:
            return None
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour < 24 and 0 <= minute < 60):
            return None
        return time(hour, minute)
    except (ValueError, AttributeError):
        return None


def parse_duration(value: Any) -> timedelta | None:
    """Parse 'HH:MM' duration. Returns None for invalid input."""
    if not value or not isinstance(value, str):
        return None
    try:
        parts = value.strip().split(":")
        if len(parts) != 2:
            return None
        hours, minutes = int(parts[0]), int(parts[1])
        return timedelta(hours=hours, minutes=minutes)
    except (ValueError, AttributeError):
        return None


ColumnMap = dict[str, str]


def _cell(row: list[Any], column_letter: str) -> Any:
    """Safely fetch a cell by column letter; returns empty string if out of bounds."""
    idx = column_letter_to_index(column_letter)
    if idx < len(row):
        return row[idx]
    return ""


def normalize_row(row: list[Any], columns: ColumnMap) -> dict[str, Any] | None:
    """Normalize one raw spreadsheet row. Returns None if no date (row is empty/header).

    Returned dict always has the same keys; missing fields are None and listed in 'issues'.
    Rows with missing duration are kept (flagged) so the report can surface gaps.
    """
    raw_date = _cell(row, columns["date"])
    parsed_date = parse_hebrew_date(raw_date)
    if parsed_date is None:
        return None  # skip rows without a valid date

    issues: list[str] = []

    from_time = parse_time(_cell(row, columns["from_time"]))
    if from_time is None:
        issues.append("from_time_missing")

    to_time = parse_time(_cell(row, columns["to_time"]))
    if to_time is None:
        issues.append("to_time_missing")

    duration = parse_duration(_cell(row, columns["duration"]))
    if duration is None:
        issues.append("duration_missing")

    client = str(_cell(row, columns["client"]) or "").strip()
    task = str(_cell(row, columns["task"]) or "").strip()
    notes = str(_cell(row, columns["notes"]) or "").strip()

    if not client:
        issues.append("client_missing")
    if not task:
        issues.append("task_missing")

    return {
        "date": parsed_date,
        "client": client,
        "task": task,
        "from_time": from_time,
        "to_time": to_time,
        "duration": duration,
        "notes": notes,
        "issues": issues,
    }


def normalize_workbook(tabs: dict[str, list[list[Any]]], config: dict[str, Any]) -> pd.DataFrame:
    """Convert a {tab_name: rows} dict into a single normalized DataFrame.

    'tabs' shape: keys are employee names, values are lists of raw spreadsheet rows.
    The 'data_start_row' from config tells us which row data begins on (1-indexed).
    """
    columns = config["sheet"]["columns"]
    data_start_row = config["sheet"].get("data_start_row", 4)
    records: list[dict[str, Any]] = []

    for employee, rows in tabs.items():
        # Convert 1-indexed data_start_row to 0-indexed slice
        for raw_row in rows[data_start_row - 1:]:
            normalized = normalize_row(raw_row, columns)
            if normalized is None:
                continue
            normalized["employee"] = employee
            records.append(normalized)

    if not records:
        return pd.DataFrame(columns=[
            "employee", "date", "client", "task", "from_time", "to_time",
            "duration", "notes", "issues",
        ])

    return pd.DataFrame(records)


def fetch_workbook(
    spreadsheet_id: str,
    tab_names: list[str],
    composio_client: Any,
) -> dict[str, list[list[Any]]]:
    """Fetch a Google Sheets workbook through the Composio Platform.

    Args:
        spreadsheet_id: The Google Sheet ID.
        tab_names: Employee tab names to read.
        composio_client: An object exposing `.execute_tool(slug, params)`
            (injected for testability). A thin adapter around the Composio SDK.

    Returns:
        Dict mapping tab name -> 2D list of raw cell values.

    The slug used is `GOOGLESHEETS_BATCH_GET` which accepts a `ranges` list.
    """
    ranges = [f"{tab}!A1:L1000" for tab in tab_names]
    result = composio_client.execute_tool(
        "GOOGLESHEETS_BATCH_GET",
        {"spreadsheetId": spreadsheet_id, "ranges": ranges},
    )
    tabs: dict[str, list[list[Any]]] = {}
    for tab_name, value_range in zip(tab_names, result.get("valueRanges", [])):
        tabs[tab_name] = value_range.get("values", [])
    return tabs

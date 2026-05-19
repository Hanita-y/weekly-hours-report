from datetime import date, time, timedelta
from unittest.mock import MagicMock

import pandas as pd

from scripts.sheets_reader import (
    column_letter_to_index,
    fetch_workbook_via_rube,
    normalize_row,
    normalize_workbook,
    parse_duration,
    parse_hebrew_date,
    parse_time,
)


# --- A: column_letter_to_index -------------------------------------------------


def test_column_letter_to_index_single():
    assert column_letter_to_index("A") == 0
    assert column_letter_to_index("L") == 11
    assert column_letter_to_index("Z") == 25


def test_column_letter_to_index_lowercase():
    assert column_letter_to_index("l") == 11


# --- B: parse_hebrew_date ------------------------------------------------------


def test_parse_hebrew_date_basic():
    assert parse_hebrew_date("13.04.26") == date(2026, 4, 13)


def test_parse_hebrew_date_single_digit_day():
    assert parse_hebrew_date("5.04.26") == date(2026, 4, 5)


def test_parse_hebrew_date_invalid_returns_none():
    assert parse_hebrew_date("") is None
    assert parse_hebrew_date("not a date") is None
    assert parse_hebrew_date(None) is None


# --- C: parse_time + parse_duration --------------------------------------------


def test_parse_time_basic():
    assert parse_time("09:15") == time(9, 15)


def test_parse_time_single_digit_hour():
    assert parse_time("9:15") == time(9, 15)


def test_parse_time_invalid_returns_none():
    assert parse_time("") is None
    assert parse_time("xx:yy") is None
    assert parse_time(None) is None


def test_parse_duration_basic():
    assert parse_duration("01:30") == timedelta(hours=1, minutes=30)
    assert parse_duration("00:15") == timedelta(minutes=15)


def test_parse_duration_long():
    assert parse_duration("12:00") == timedelta(hours=12)


def test_parse_duration_invalid_returns_none():
    assert parse_duration("") is None
    assert parse_duration("xx") is None
    assert parse_duration(None) is None


# --- D: normalize_row ----------------------------------------------------------


def test_normalize_row_complete():
    row = ["", "", "", "", "", "", "01:40", "12:00", "10:20", "ישיבת צוות", "משרד", "12.04.26"]
    columns = {"date": "L", "client": "K", "task": "J", "from_time": "I", "to_time": "H", "duration": "G", "notes": "F"}
    result = normalize_row(row, columns)
    assert result["date"] == date(2026, 4, 12)
    assert result["client"] == "משרד"
    assert result["task"] == "ישיבת צוות"
    assert result["from_time"] == time(10, 20)
    assert result["to_time"] == time(12, 0)
    assert result["duration"] == timedelta(hours=1, minutes=40)
    assert result["notes"] == ""
    assert result["issues"] == []


def test_normalize_row_missing_duration():
    row = ["", "", "", "", "", "", "", "10:00", "09:00", "פגישה", "משרד", "14.04.26"]
    columns = {"date": "L", "client": "K", "task": "J", "from_time": "I", "to_time": "H", "duration": "G", "notes": "F"}
    result = normalize_row(row, columns)
    assert result["date"] == date(2026, 4, 14)
    assert result["duration"] is None
    assert "duration_missing" in result["issues"]


def test_normalize_row_no_date_returns_none():
    row = ["", "", "", "", "", "", "", "", "", "", "", ""]
    columns = {"date": "L", "client": "K", "task": "J", "from_time": "I", "to_time": "H", "duration": "G", "notes": "F"}
    result = normalize_row(row, columns)
    assert result is None


# --- E: normalize_workbook -----------------------------------------------------


def test_normalize_workbook(sample_sheet_data, default_config):
    df = normalize_workbook(sample_sheet_data["tabs"], default_config)
    assert isinstance(df, pd.DataFrame)
    expected_columns = {"employee", "date", "client", "task", "from_time", "to_time", "duration", "notes", "issues"}
    assert expected_columns.issubset(df.columns)
    # Two employees in fixture
    assert set(df["employee"].unique()) == {"אופיר", "אביב"}
    # אופיר has dates in both reference and previous weeks
    assert df[df["employee"] == "אופיר"]["date"].min() == date(2026, 4, 5)
    # The row with missing duration (14.04.26 אופיר) should be present and flagged
    ofir_14 = df[(df["employee"] == "אופיר") & (df["date"] == date(2026, 4, 14))]
    assert len(ofir_14) == 1
    assert "duration_missing" in ofir_14.iloc[0]["issues"]


# --- F: fetch_workbook_via_rube ------------------------------------------------


def test_fetch_workbook_via_rube_passes_correct_ranges():
    mock_client = MagicMock()
    mock_client.execute_tool.return_value = {
        "valueRanges": [
            {"values": [["row1"]]},
            {"values": [["row2"]]},
        ]
    }
    result = fetch_workbook_via_rube("SHEET_ID", ["אופיר", "אביב"], mock_client)
    mock_client.execute_tool.assert_called_once_with(
        "GOOGLESHEETS_BATCH_GET",
        {"spreadsheetId": "SHEET_ID", "ranges": ["אופיר!A1:L1000", "אביב!A1:L1000"]},
    )
    assert result == {"אופיר": [["row1"]], "אביב": [["row2"]]}

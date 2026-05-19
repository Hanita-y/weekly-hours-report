import json
from pathlib import Path
from datetime import date

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_sheet_data():
    """Loads the canonical sample sheet fixture."""
    with open(FIXTURES_DIR / "sample_sheet.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def reference_week():
    """The 'last week' for tests: Sunday 2026-04-12 through Saturday 2026-04-18."""
    return (date(2026, 4, 12), date(2026, 4, 18))


@pytest.fixture
def prev_reference_week():
    """The 'previous week' for tests: Sunday 2026-04-05 through Saturday 2026-04-11."""
    return (date(2026, 4, 5), date(2026, 4, 11))


@pytest.fixture
def default_config():
    """Default configuration matching config.example.json."""
    return {
        "sheet": {
            "spreadsheet_id": "TEST_SHEET_ID",
            "employee_tabs": ["אופיר", "אביב"],
            "data_start_row": 5,
            "columns": {
                "date": "L",
                "client": "K",
                "task": "J",
                "from_time": "I",
                "to_time": "H",
                "duration": "G",
                "notes": "F",
            },
            "date_format": "DD.MM.YY",
        },
        "email": {
            "recipient": "test@example.com",
            "cc": [],
            "subject_template": "דוח שעות שבועי | {date_range} | {total_hours}",
        },
        "schedule": {
            "cron": "0 8 * * 0",
            "timezone": "Asia/Jerusalem",
            "comment": "ראשון 08:00",
        },
        "anomaly_thresholds": {
            "long_task_hours": 3,
            "schedule_gap_minutes": 30,
            "underreporting_daily_hours": 6,
            "overreporting_daily_hours": 10,
        },
        "workdays": ["sunday", "monday", "tuesday", "wednesday", "thursday"],
        "branding": {"footer_text": "Hours Tracker · אוטומציה שבועית"},
    }

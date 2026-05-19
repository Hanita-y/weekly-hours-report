"""Orchestrator: load config, fetch sheet, build report, render, send.

Configuration sources:
  1. `config.json` next to this file (local runs, created by `setup.py`).
  2. Environment variables (for CI / GitHub Actions runs). Required vars:
       COMPOSIO_API_KEY, SHEET_ID, EMPLOYEE_TABS (JSON array), RECIPIENT_EMAIL
     Optional:
       CC_EMAILS (comma-separated), TZ (default "Asia/Jerusalem")

If `config.json` exists it wins. Otherwise env-var mode is used.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("weekly-hours-report")

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "config.json"
EXAMPLE_PATH = SKILL_ROOT / "config.example.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing config.json. Run `python scripts/setup.py` first. Expected at: {path}"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_example_defaults() -> dict:
    """Load config.example.json as the baseline for env-var mode defaults."""
    with open(EXAMPLE_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_config_from_env() -> dict:
    """Build a config dict from environment variables.

    Used in CI / GitHub Actions where we don't ship a config.json file.
    Pulls user-specific values from env, copies all other defaults
    (columns, anomaly_thresholds, workdays, branding) from config.example.json.
    """
    required = {
        "SHEET_ID": "Google Sheet ID",
        "EMPLOYEE_TABS": "JSON array of employee tab names",
        "RECIPIENT_EMAIL": "Recipient email address",
    }
    missing = [k for k in required if not os.environ.get(k)]
    if not os.environ.get("COMPOSIO_API_KEY"):
        missing.insert(0, "COMPOSIO_API_KEY")
    if missing:
        raise RuntimeError(
            "Environment-variable config mode requires: "
            + ", ".join(missing)
            + ". Either set them or create a config.json via `python scripts/setup.py`."
        )

    cfg = _load_example_defaults()

    cfg["sheet"]["spreadsheet_id"] = os.environ["SHEET_ID"]
    try:
        tabs = json.loads(os.environ["EMPLOYEE_TABS"])
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"EMPLOYEE_TABS must be a JSON array string like '[\"אופיר\",\"אביב\"]'. Got error: {e}"
        )
    if not isinstance(tabs, list) or not all(isinstance(t, str) for t in tabs):
        raise RuntimeError("EMPLOYEE_TABS must be a JSON array of strings.")
    cfg["sheet"]["employee_tabs"] = tabs

    cfg["email"]["recipient"] = os.environ["RECIPIENT_EMAIL"]
    cc_raw = os.environ.get("CC_EMAILS", "").strip()
    cfg["email"]["cc"] = [c.strip() for c in cc_raw.split(",") if c.strip()] if cc_raw else []

    cfg["schedule"]["timezone"] = os.environ.get("TZ", cfg["schedule"].get("timezone", "Asia/Jerusalem"))

    return cfg


def get_composio_client():
    """Construct the Composio client for use in this run.

    The Composio Python SDK is initialized using the COMPOSIO_API_KEY env var.
    """
    from composio import Composio  # type: ignore

    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        raise RuntimeError(
            "COMPOSIO_API_KEY env var is not set. "
            "Composio Platform API key is required — see https://composio.dev"
        )

    client = Composio(api_key=api_key)

    class _Adapter:
        def __init__(self, c):
            self._c = c

        def execute_tool(self, slug: str, params: dict):
            return self._c.actions.execute(action=slug, params=params)

    return _Adapter(client)


def main() -> int:
    if CONFIG_PATH.exists():
        config = load_config()
    else:
        config = load_config_from_env()

    tz = pytz.timezone(config["schedule"]["timezone"])
    now_local = datetime.now(tz)
    today: date = now_local.date()
    log.info("Starting weekly report run for %s", today.isoformat())

    try:
        composio = get_composio_client()

        from scripts.sheets_reader import fetch_workbook, normalize_workbook
        from scripts.analyzer import build_report
        from scripts.renderer import render_email_html, render_pdf_bytes
        from scripts.mailer import send_report

        tabs = fetch_workbook(
            config["sheet"]["spreadsheet_id"],
            config["sheet"]["employee_tabs"],
            composio,
        )
        df = normalize_workbook(tabs, config)
        report = build_report(df, today, config)
        html = render_email_html(report, config, now_local.replace(tzinfo=None))
        pdf = render_pdf_bytes(report, config, now_local.replace(tzinfo=None))

        from scripts.renderer import _subject  # noqa: SLF001 — internal helper reuse
        subject = _subject(report, config)
        filename = f"weekly-hours-{today.strftime('%Y-%m-%d')}.pdf"

        result = send_report(
            composio_client=composio,
            sender=config["email"]["recipient"],  # Gmail uses authenticated user as From
            recipient=config["email"]["recipient"],
            cc=config["email"].get("cc", []),
            subject=subject,
            html=html,
            pdf_bytes=pdf,
            pdf_filename=filename,
        )
        log.info("Sent message id=%s", result.get("id"))
        return 0

    except Exception:  # noqa: BLE001
        tb = traceback.format_exc()
        log.error("Report run failed:\n%s", tb)
        try:
            _send_failure_notice(config, tb, today)
        except Exception as inner:  # noqa: BLE001
            log.error("Could not send failure notice: %s", inner)
        return 1


def _send_failure_notice(config: dict, tb: str, today: date) -> None:
    """Best-effort: notify the recipient that the report run failed."""
    composio = get_composio_client()
    from scripts.mailer import build_mime_message
    html = (
        "<p dir='rtl'>הדוח השבועי לא נשלח עקב שגיאה.</p>"
        f"<pre>{tb}</pre>"
    )
    raw = build_mime_message(
        sender=config["email"]["recipient"],
        recipient=config["email"]["recipient"],
        cc=[],
        subject=f"דוח שבועי נכשל — {today.strftime('%d.%m.%y')}",
        html=html,
        pdf_bytes=b"",  # no attachment for failure notice
        pdf_filename="failure.pdf",
    )
    composio.execute_tool("GMAIL_SEND_EMAIL", {"raw": raw})


if __name__ == "__main__":
    sys.exit(main())

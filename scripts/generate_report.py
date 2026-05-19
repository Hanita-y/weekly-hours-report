"""Orchestrator: load config, fetch sheet, build report, render, send."""
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


def load_config(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing config.json. Run `python scripts/setup.py` first. Expected at: {path}"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_rube_client():
    """Construct the Rube/Composio client for use in this run.

    The Composio Python SDK is initialized using the COMPOSIO_API_KEY env var.
    """
    from composio import Composio  # type: ignore

    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        raise RuntimeError(
            "COMPOSIO_API_KEY env var is not set. "
            "Rube/Composio API key is required — see https://rube.app"
        )

    client = Composio(api_key=api_key)

    class _Adapter:
        def __init__(self, c):
            self._c = c

        def execute_tool(self, slug: str, params: dict):
            return self._c.actions.execute(action=slug, params=params)

    return _Adapter(client)


def main() -> int:
    config = load_config()
    tz = pytz.timezone(config["schedule"]["timezone"])
    now_local = datetime.now(tz)
    today: date = now_local.date()
    log.info("Starting weekly report run for %s", today.isoformat())

    try:
        rube = get_rube_client()

        from scripts.sheets_reader import fetch_workbook_via_rube, normalize_workbook
        from scripts.analyzer import build_report
        from scripts.renderer import render_email_html, render_pdf_bytes
        from scripts.mailer import send_report

        tabs = fetch_workbook_via_rube(
            config["sheet"]["spreadsheet_id"],
            config["sheet"]["employee_tabs"],
            rube,
        )
        df = normalize_workbook(tabs, config)
        report = build_report(df, today, config)
        html = render_email_html(report, config, now_local.replace(tzinfo=None))
        pdf = render_pdf_bytes(report, config, now_local.replace(tzinfo=None))

        from scripts.renderer import _subject  # noqa: SLF001 — internal helper reuse
        subject = _subject(report, config)
        filename = f"weekly-hours-{today.strftime('%Y-%m-%d')}.pdf"

        result = send_report(
            rube_client=rube,
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
    rube = get_rube_client()
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
    rube.execute_tool("GMAIL_SEND_EMAIL", {"raw": raw})


if __name__ == "__main__":
    sys.exit(main())

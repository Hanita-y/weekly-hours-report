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


def _discover_user_id(client) -> str:
    """Find the user_id whose Composio account has BOTH googlesheets AND gmail connected.

    Returns the user_id. Raises a clear RuntimeError if no such user is found.
    """
    accounts = client.connected_accounts.list()
    items = accounts.items if hasattr(accounts, "items") else accounts

    user_toolkits: dict[str, set[str]] = {}
    for a in items:
        user_id = getattr(a, "user_id", None)
        toolkit = getattr(a, "toolkit", None)
        toolkit_slug = getattr(toolkit, "slug", None) if toolkit else None
        status = getattr(a, "status", None)
        if not user_id or not toolkit_slug or status != "ACTIVE":
            continue
        user_toolkits.setdefault(user_id, set()).add(toolkit_slug)

    candidates = [
        uid for uid, kits in user_toolkits.items()
        if "googlesheets" in kits and "gmail" in kits
    ]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise RuntimeError(
            "No Composio user found with BOTH Google Sheets and Gmail connections. "
            "Set up both Auth Configs at https://platform.composio.dev/auth-configs "
            "and click 'Connect Account' on each. Then set COMPOSIO_USER_ID env var "
            "explicitly, or re-run after connecting."
        )
    raise RuntimeError(
        f"Multiple Composio users have both connections: {candidates}. "
        f"Set COMPOSIO_USER_ID env var explicitly to pick one."
    )


def get_composio_client():
    """Construct the Composio client for use in this run.

    The Composio Python SDK is initialized using the COMPOSIO_API_KEY env var.
    The COMPOSIO_USER_ID env var is optional — if not set (or set to "default"),
    the user_id is auto-discovered from connected accounts that have BOTH
    Google Sheets and Gmail toolkits active.
    """
    from composio import Composio  # type: ignore

    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        raise RuntimeError(
            "COMPOSIO_API_KEY env var is not set. "
            "Composio Platform API key is required — see https://composio.dev"
        )

    client = Composio(api_key=api_key)
    user_id = os.environ.get("COMPOSIO_USER_ID")
    if not user_id or user_id == "default":
        user_id = _discover_user_id(client)
        log.info("Auto-discovered Composio user_id: %s", user_id)

    class _Adapter:
        def __init__(self, c, user_id):
            self._c = c
            self._user_id = user_id

        def execute_tool(self, slug: str, params: dict):
            return self._c.tools.execute(
                slug,
                params,
                user_id=self._user_id,
                dangerously_skip_version_check=True,
            )

    return _Adapter(client, user_id)


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
        msg_id = (result.get("data") or {}).get("id") if isinstance(result, dict) else None
        log.info("Sent message id=%s", msg_id)
        if isinstance(result, dict) and result.get("successful") is False:
            log.warning("Composio reported successful=False: %s", result.get("error"))
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
    html = (
        "<p dir='rtl'>הדוח השבועי לא נשלח עקב שגיאה.</p>"
        f"<pre>{tb}</pre>"
    )
    composio.execute_tool(
        "GMAIL_SEND_EMAIL",
        {
            "recipient_email": config["email"]["recipient"],
            "subject": f"דוח שבועי נכשל — {today.strftime('%d.%m.%y')}",
            "body": html,
            "is_html": True,
        },
    )


if __name__ == "__main__":
    sys.exit(main())

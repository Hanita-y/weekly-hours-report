---
name: weekly-hours-report
description: Weekly automated employee hours report. Reads a Hebrew Google Sheets workbook with one tab per employee, aggregates the prior week's data, detects anomalies (missing data, schedule gaps, over/under reporting), and emails an HTML report every Sunday 08:00 Israel time. Setup uses Composio for OAuth (Google Sheets + Gmail). Scheduling runs via GitHub Actions cron.
---

# Weekly Hours Report

Use this skill when a user wants to set up automated weekly time-tracking reports from a Google Sheets workbook formatted with one tab per employee and columns for date, client, task, start/end time, total duration, and notes.

## Setup

1. Sign up at https://composio.dev and create Auth Configs for **Google Sheets** and **Gmail**, then connect a Google account to each.
2. Generate a Composio API key and export it: `export COMPOSIO_API_KEY=...`
3. Run `python scripts/setup.py` from the skill folder. It will:
   - Verify `COMPOSIO_API_KEY` is set.
   - Prompt for the sheet ID, employee tab names, recipient email, and schedule.
   - Write `config.json`.
   - Optionally send a test report immediately.

Full step-by-step guide with screenshots: [docs/setup-guide-he.md](docs/setup-guide-he.md).

## Manual report

Run `python -m scripts.generate_report` (from the skill root) to send the current week's report on demand.

## Weekly cron

Scheduling is handled by **GitHub Actions** (not Composio). Fork the repo, add Repository Secrets (`COMPOSIO_API_KEY`, `SHEET_ID`, `EMPLOYEE_TABS`, `RECIPIENT_EMAIL`, optionally `CC_EMAILS`, optionally `COMPOSIO_USER_ID`), and `.github/workflows/weekly-report.yml` will run the report every Sunday 08:00 IL. If `COMPOSIO_USER_ID` is not set, the script auto-discovers it from connected accounts that have both Google Sheets and Gmail toolkits active.

## Files

- `config.json` — user configuration (gitignored). Template is `config.example.json`.
- `scripts/` — pipeline modules.
- `templates/` — Jinja2 HTML + CSS for the email body.
- `tests/` — pytest suite, fixture-based.
- `.github/workflows/weekly-report.yml` — weekly cron on GitHub Actions.
- `docs/setup-guide-he.md` — step-by-step setup guide in Hebrew with Composio screenshots.

## Requires

- Python 3.11+
- Composio Platform account (https://composio.dev) with Auth Configs connected for Google Sheets + Gmail
- Google account with access to the target Sheets workbook
- (For weekly cron) GitHub account with the repo forked

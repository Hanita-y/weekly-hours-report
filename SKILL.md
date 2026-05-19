---
name: weekly-hours-report
description: Weekly automated employee hours report. Reads a Hebrew Google Sheets workbook with one tab per employee, aggregates the prior week's data, detects anomalies (missing data, schedule gaps, over/under reporting), and emails an HTML + PDF report every Sunday 08:00 Israel time. Setup uses Rube/Composio for OAuth and scheduling.
---

# Weekly Hours Report

Use this skill when a user wants to set up automated weekly time-tracking reports from a Google Sheets workbook formatted with one tab per employee and columns for date, client, task, start/end time, total duration, and notes.

## Setup

Run `python scripts/setup.py` from the skill folder. It will:

1. Verify Rube (rube.app) is connected.
2. OAuth-connect Google Sheets and Gmail through Rube.
3. Prompt for the sheet ID, employee tab names, recipient email, and schedule.
4. Write `config.json`.
5. Create a Composio recipe and register the Sunday-08:00 cron.
6. Optionally send a test report immediately.

## Manual report

Run `python scripts/generate_report.py` to send the current week's report on demand.

## Files

- `config.json` — user configuration (gitignored). Template is `config.example.json`.
- `scripts/` — pipeline modules.
- `templates/` — Jinja2 HTML + CSS for email and PDF.
- `tests/` — pytest suite, fixture-based.
- `docs/setup-guide-he.md` — step-by-step setup guide in Hebrew.

## Requires

- Python 3.11+
- Rube/Composio account (https://rube.app)
- Google account with access to the target Sheets workbook

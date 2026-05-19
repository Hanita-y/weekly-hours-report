# Weekly Hours Report

[![Powered by Composio](https://img.shields.io/badge/Powered_by-Composio-blue?style=flat-square)](https://composio.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

A Claude Code skill that emails a weekly Hebrew hours report from a Google Sheets workbook with one tab per employee. Runs every Sunday 08:00 (Israel time) via GitHub Actions cron, using the **Composio Platform** for Google Sheets + Gmail OAuth.

> **Requires [Composio Platform](https://composio.dev).** Composio provides the OAuth layer (Auth Configs) for Google Sheets and Gmail. Scheduling runs on **GitHub Actions** — fork the repo, add Repository Secrets, and the weekly cron runs automatically.

## Quick start

```bash
git clone https://github.com/Hanita-y/weekly-hours-report.git ~/.claude/skills/weekly-hours-report
cd ~/.claude/skills/weekly-hours-report
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export COMPOSIO_API_KEY=...
python scripts/setup.py
```

To enable the weekly cron, fork the repo and add the following Repository Secrets:
- `COMPOSIO_API_KEY`
- `SHEET_ID`
- `EMPLOYEE_TABS` (JSON array string, e.g. `["Ofir","Aviv"]`)
- `RECIPIENT_EMAIL`
- `CC_EMAILS` (optional, comma-separated)
- `COMPOSIO_USER_ID` (optional — auto-discovered from connected accounts if not set)

To run the report manually (from the skill root):

```bash
python -m scripts.generate_report
```

See [README.md](README.md) (Hebrew) for full documentation and [docs/setup-guide-he.md](docs/setup-guide-he.md) for the step-by-step Composio Platform UI walkthrough.

## License

MIT — see [LICENSE](LICENSE).

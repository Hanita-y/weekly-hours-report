# Weekly Hours Report

[![Powered by Rube](https://img.shields.io/badge/Powered_by-Rube-blue?style=flat-square)](https://rube.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

A Claude Code skill that emails a weekly Hebrew hours report from a Google Sheets workbook with one tab per employee. Runs every Sunday 08:00 (Israel time) via a Rube/Composio scheduled recipe.

> **Requires [Rube by Composio](https://rube.app).** Rube provides OAuth for Google Sheets + Gmail and the cron + sandbox that runs the pipeline. The skill will not function without it.

## Quick start

```bash
git clone https://github.com/Hanita-y/weekly-hours-report.git ~/.claude/skills/weekly-hours-report
cd ~/.claude/skills/weekly-hours-report
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export COMPOSIO_API_KEY=...
python scripts/setup.py
```

See [README.md](README.md) (Hebrew) for full documentation.

## License

MIT — see [LICENSE](LICENSE).

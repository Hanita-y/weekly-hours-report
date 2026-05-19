# Weekly Hours Report

[![Powered by Rube](https://img.shields.io/badge/Powered_by-Rube-blue?style=flat-square)](https://rube.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

סקיל ל-Claude Code שמייצר אוטומטית דוח שעות שבועי עברי ושולח אותו במייל כל ראשון בבוקר. הסקיל קורא Google Sheets שבו כל עובד מקבל טאב משלו, מסכם את השבוע האחרון, מזהה חריגות (מידע חסר, ימים ללא דיווח, פעולות ארוכות, דיווח נמוך/גבוה), ושולח Gmail עם גוף HTML מינימליסטי + PDF מצורף.

> **דרישה חיונית: [Rube by Composio](https://rube.app)** — Rube מספק את שכבת ה-OAuth ל-Google Sheets + Gmail וגם את ה-cron + ה-sandbox שמריץ את הסקיל אוטומטית. ללא Rube הסקיל לא יעבוד.

---

## דרישות מקדימות

1. **Python 3.11+**
2. **Rube account** — בחינם דרך [rube.app](https://rube.app).
3. **חיבור Rube ל-Claude Code** — ראו ההוראות ב-rube.app אחרי ההרשמה.
4. **חשבון Google** עם גישה לטבלת השעות.

---

## התקנה

```bash
git clone https://github.com/Hanita-y/weekly-hours-report.git ~/.claude/skills/weekly-hours-report
cd ~/.claude/skills/weekly-hours-report
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export COMPOSIO_API_KEY=your_rube_api_key_here
python scripts/setup.py
```

ה-`setup.py` יבקש:
- מזהה ה-Google Sheet (מתוך ה-URL)
- שמות הטאבים (אחד לכל עובד)
- כתובת מייל ליעד
- שעה לשליחה (ברירת מחדל ראשון 08:00)

ואז הוא:
- מתחבר ל-Google Sheets + Gmail דרך Rube (OAuth בדפדפן)
- כותב `config.json` מקומי
- יוצר Composio recipe + רושם את ה-cron
- שולח דוח test אופציונלי

---

## מבנה הסקיל

```
weekly-hours-report/
├── SKILL.md                # תיעוד Claude
├── README.md               # מסמך זה (עברית)
├── README.en.md            # English
├── LICENSE                 # MIT
├── requirements.txt
├── config.example.json     # תבנית config
├── scripts/                # generate_report, sheets_reader, analyzer,
│                           # renderer, mailer, setup
├── templates/              # email.html, pdf.html, styles.css
├── tests/                  # pytest suite
└── docs/
    ├── setup-guide-he.md   # מדריך התקנה צעד-צעד עם צילומי מסך
    ├── customization.md
    └── troubleshooting.md
```

---

## הרצה ידנית

```bash
python scripts/generate_report.py
```

---

## שינוי תצורה

ערוך את `config.json` (לא נכנס ל-Git). שדות נפוצים:

- `email.recipient` — מייל היעד
- `email.cc` — עותקים נוספים
- `schedule.cron` — מתי לשלוח (פורמט cron)
- `anomaly_thresholds` — סף לחריגות
- `workdays` — ימי עבודה (קובע "מידע חסר" לפי יום)

ראו [docs/customization.md](docs/customization.md) להרחבה.

---

## סדנא ולמידה

הסקיל הזה נבנה כחלק מסדנא של Hanita ו-Sean למשרדי סושיאל. הוא חינמי לשימוש ולשינוי תחת רישיון MIT.

---

## רישיון

MIT — ראו [LICENSE](LICENSE).

---

## תודות

- [Rube by Composio](https://rube.app) — שכבת האינטגרציה
- Google Fonts — פונט [Assistant](https://fonts.google.com/specimen/Assistant)
- [WeasyPrint](https://weasyprint.org/) — יצירת PDF

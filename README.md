# Weekly Hours Report

[![Powered by Composio](https://img.shields.io/badge/Powered_by-Composio-blue?style=flat-square)](https://composio.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

סקיל ל-Claude Code שמייצר אוטומטית דוח שעות שבועי עברי ושולח אותו במייל כל ראשון בבוקר. הסקיל קורא Google Sheets שבו כל עובד מקבל טאב משלו, מסכם את השבוע האחרון, מזהה חריגות (מידע חסר, ימים ללא דיווח, פעולות ארוכות, דיווח נמוך/גבוה), ושולח Gmail עם גוף HTML מינימליסטי + PDF מצורף.

> **דרישה חיונית: [Composio Platform](https://composio.dev)** — Composio מספק את שכבת ה-OAuth ל-Google Sheets + Gmail (Auth Configs מנוהלים). ה-cron השבועי רץ דרך **GitHub Actions** (לא דרך Composio) — ראי [docs/setup-guide-he.md](docs/setup-guide-he.md) למדריך מלא עם צילומי מסך.

---

## דרישות מקדימות

1. **Python 3.11+**
2. **Composio account** — בחינם דרך [composio.dev](https://composio.dev).
3. **חשבון GitHub** — אם רוצים cron אוטומטי שבועי (פורקים את הריפו).
4. **חשבון Google** עם גישה לטבלת השעות.

---

## התקנה

```bash
git clone https://github.com/Hanita-y/weekly-hours-report.git ~/.claude/skills/weekly-hours-report
cd ~/.claude/skills/weekly-hours-report
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export COMPOSIO_API_KEY=your_composio_api_key_here
python scripts/setup.py
```

ה-`setup.py` יבקש:
- מזהה ה-Google Sheet (מתוך ה-URL)
- שמות הטאבים (אחד לכל עובד)
- כתובת מייל ליעד
- שעה לשליחה (ברירת מחדל ראשון 08:00 — רלוונטי בעיקר ל-cron של GitHub Actions)

ואז הוא:
- כותב `config.json` מקומי
- מציע לשלוח דוח test מיידי

לחיבור OAuth ל-Google Sheets + Gmail יש להיכנס ל-[composio.dev](https://composio.dev), להוסיף Auth Configs ל-Google Sheets ו-Gmail, ולחבר חשבון Google דרך הממשק. ראי [docs/setup-guide-he.md](docs/setup-guide-he.md) למדריך מסודר.

---

## תזמון שבועי אוטומטי (cron)

הסקיל אינו רץ על תשתית של Composio — Composio מנהל רק את שכבת ה-API. את התזמון השבועי מבצעים דרך **GitHub Actions**:

1. עשי Fork לריפו ב-GitHub.
2. ב-Settings → Secrets and variables → Actions, הוסיפי Repository Secrets:
   - `COMPOSIO_API_KEY`
   - `SHEET_ID`
   - `EMPLOYEE_TABS` (מחרוזת JSON, למשל `["אופיר","אביב"]`)
   - `RECIPIENT_EMAIL`
   - `CC_EMAILS` (אופציונלי, מופרד בפסיק)
   - `COMPOSIO_USER_ID` (אופציונלי — אם לא תוסיפי, יתגלה אוטומטית מה-Connected Accounts שלך)
3. ה-workflow `.github/workflows/weekly-report.yml` ירוץ ראשון 08:00 שעון ישראל אוטומטית.

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
├── .github/workflows/
│   ├── tests.yml           # CI לבדיקות
│   └── weekly-report.yml   # cron שבועי
└── docs/
    ├── setup-guide-he.md   # מדריך התקנה צעד-צעד עם צילומי מסך
    ├── customization.md
    └── troubleshooting.md
```

---

## הרצה ידנית

```bash
python -m scripts.generate_report   # NOT: python scripts/generate_report.py
```

(הריצי תמיד משורש התיקייה של הסקיל, כדי ש-Python ימצא את החבילה.)

---

## שינוי תצורה

ערכי את `config.json` (לא נכנס ל-Git). שדות נפוצים:

- `email.recipient` — מייל היעד
- `email.cc` — עותקים נוספים
- `schedule.cron` — מתי לשלוח (פורמט cron — רלוונטי ל-GitHub Actions)
- `anomaly_thresholds` — סף לחריגות
- `workdays` — ימי עבודה (קובע "מידע חסר" לפי יום)

ראי [docs/customization.md](docs/customization.md) להרחבה.

---

## סדנא ולמידה

הסקיל הזה נבנה כחלק מסדנא של Hanita ו-Sean למשרדי סושיאל. הוא חינמי לשימוש ולשינוי תחת רישיון MIT.

---

## רישיון

MIT — ראי [LICENSE](LICENSE).

---

## תודות

- [Composio Platform](https://composio.dev) — שכבת האינטגרציה ל-Google Sheets ו-Gmail
- GitHub Actions — תשתית cron שבועית
- Google Fonts — פונט [Assistant](https://fonts.google.com/specimen/Assistant)
- [WeasyPrint](https://weasyprint.org/) — יצירת PDF

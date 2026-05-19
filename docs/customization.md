# התאמה אישית

כל הגדרה בקובץ `config.json`. אחרי כל שינוי הריצי `python -m scripts.generate_report` לבדיקה (משורש התיקייה).

## שינוי מייל יעד

```json
"email": {
  "recipient": "new-email@company.com",
  "cc": ["manager@company.com"]
}
```

## שינוי לוח הזמנים

`schedule.cron` בפורמט cron. דוגמאות:

- `"0 8 * * 0"` — ראשון 08:00
- `"0 9 * * 1"` — שני 09:00
- `"0 18 * * 5"` — חמישי 18:00

אם משתמשים ב-GitHub Actions cron — עדכני את ה-cron גם בקובץ `.github/workflows/weekly-report.yml` (בשורת `cron:` תחת `schedule`). שימי לב שהזמן שם ב-UTC ולא בשעון ישראל.

## שינוי מבנה הטבלה

אם הטבלה שלך עם עמודות אחרות:

```json
"sheet": {
  "columns": {
    "date": "A",
    "client": "B",
    "task": "C",
    "from_time": "D",
    "to_time": "E",
    "duration": "F",
    "notes": "G"
  },
  "data_start_row": 2
}
```

## שינוי סף חריגות

```json
"anomaly_thresholds": {
  "long_task_hours": 4,
  "schedule_gap_minutes": 60,
  "underreporting_daily_hours": 5,
  "overreporting_daily_hours": 12
}
```

## שינוי ימי עבודה

```json
"workdays": ["sunday", "monday", "tuesday", "wednesday", "thursday"]
```

הסר ימים שאינם ימי עבודה (למשל "thursday" אם עובדים רק עד רביעי).

## שינוי טקסט ה-footer

```json
"branding": {
  "footer_text": "החברה שלי · אוטומציה שבועית"
}
```

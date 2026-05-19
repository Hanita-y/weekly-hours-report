# פתרון תקלות

## הדוח לא הגיע

1. בדקי שה-cron רץ ב-Rube dashboard. כל recipe מופיע שם עם היסטוריית הרצות.
2. בדקי לוגים: `python scripts/generate_report.py` (הרצה ידנית) — תראי את השגיאה.
3. ודאי ש-`COMPOSIO_API_KEY` מוגדר.

## "COMPOSIO_API_KEY is not set"

```bash
export COMPOSIO_API_KEY="..."
```

הוסיפי לקובץ `~/.zshrc` (Mac) או `~/.bashrc` (Linux) כדי שיישמר בין sessions.

## "Permission denied" ל-Google Sheets

הריצי שוב את `setup.py` — הוא ייצור חיבור חדש. או ב-Rube dashboard → Connections → מחקי את החיבור הישן והוסיפי חדש.

## ה-PDF נראה שבור (עברית הפוכה / פונט חסר)

WeasyPrint דורש libcairo, libpango. ב-Mac:
```bash
brew install cairo pango gdk-pixbuf libffi
```

ב-Linux Ubuntu:
```bash
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```

## "Quota exceeded" של Google Sheets

קורה רק אם הטבלה ענקית (>50K שורות) או הרבה משתמשים על אותו project. בדרך כלל ה-skill לא מגיע למצב הזה.

## טבלה לא נטענת

ודאי שה-`spreadsheet_id` ב-config.json נכון. הוא הקטע בין `/d/` ל-`/edit` ב-URL של הטבלה.

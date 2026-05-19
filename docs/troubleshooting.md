# פתרון תקלות

## הדוח לא הגיע

1. אם הוגדר cron אוטומטי דרך GitHub Actions — היכנסי לטאב **Actions** של הריפו ב-GitHub וראי אם הריצה האחרונה הצליחה או נכשלה. בלוגים תראי בדיוק איפה זה נשבר.
2. בדקי את ה-Connections ב-[Composio Platform dashboard](https://composio.dev) — צריך לראות חשבון Google מחובר ל-Auth Config של Google Sheets וגם ל-Auth Config של Gmail.
3. הרצה ידנית: `python scripts/generate_report.py` תציג את השגיאה ב-stderr.
4. ודאי ש-`COMPOSIO_API_KEY` מוגדר (מקומית או כ-Repository Secret ב-GitHub).

## "COMPOSIO_API_KEY is not set"

```bash
export COMPOSIO_API_KEY="..."
```

הוסיפי לקובץ `~/.zshrc` (Mac) או `~/.bashrc` (Linux) כדי שיישמר בין sessions.

ב-GitHub Actions זה לא משתנה סביבה גלובלי — צריך להגדיר Repository Secret בשם `COMPOSIO_API_KEY` ב-Settings → Secrets and variables → Actions.

## "Permission denied" ל-Google Sheets

החיבור פג או נמחק. כנסי ל-Composio Platform → Auth Configs → לחצי על Google Sheets → Connect Account ותחברי חשבון Google מחדש (עוברים שוב על מסך ההרשאות של Google).

## ה-PDF נראה שבור (עברית הפוכה / פונט חסר)

WeasyPrint דורש libcairo, libpango. ב-Mac:
```bash
brew install cairo pango gdk-pixbuf libffi
```

ב-Linux Ubuntu:
```bash
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```

ב-GitHub Actions זה כבר מותקן אוטומטית דרך ה-workflow.

## "Quota exceeded" של Google Sheets

קורה רק אם הטבלה ענקית (>50K שורות) או הרבה משתמשים על אותו project. בדרך כלל ה-skill לא מגיע למצב הזה.

## טבלה לא נטענת

ודאי שה-`spreadsheet_id` ב-config.json נכון. הוא הקטע בין `/d/` ל-`/edit` ב-URL של הטבלה.

## ה-cron של GitHub Actions לא רץ

- ודאי ש-Workflows מופעלים בריפו (Settings → Actions → Allow all actions).
- אם הריפו פרטי ולא היה פעיל יותר מ-60 ימים, GitHub משבית את ה-cron אוטומטית. תני push קל כדי להעיר אותו.
- אפשר להריץ ידנית: Actions → weekly-report → Run workflow.

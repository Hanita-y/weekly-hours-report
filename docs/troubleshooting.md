# פתרון תקלות

## הדוח לא הגיע

1. אם הוגדר cron אוטומטי דרך GitHub Actions — היכנסי לטאב **Actions** של הריפו ב-GitHub וראי אם הריצה האחרונה הצליחה או נכשלה. בלוגים תראי בדיוק איפה זה נשבר.
2. בדקי את ה-Connections ב-[Composio Platform dashboard](https://composio.dev) — צריך לראות חשבון Google מחובר ל-Auth Config של Google Sheets וגם ל-Auth Config של Gmail.
3. הרצה ידנית: `python -m scripts.generate_report` (משורש התיקייה) תציג את השגיאה ב-stderr.
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

---

## תקלות שעלו בבדיקה החיה — תיקונים נפוצים

### "AttributeError: 'Composio' object has no attribute 'actions'"

ה-Composio SDK עבר ל-API חדש (`c.tools.execute`). אם רואה את השגיאה ודאי שאת על `composio>=0.13.1`:

```bash
pip install --upgrade composio
```

### "ToolVersionRequiredError: Toolkit version not specified"

הסקריפט מטפל בזה אוטומטית עם `dangerously_skip_version_check=True`. אם רואה את השגיאה ודאי שיש לך את הגרסה האחרונה של הסקיל (`git pull` בריפו).

### "No connected account found for user ID ... for toolkit googlesheets"

חסר חיבור פעיל. שני תיקונים אפשריים:

1. ודאי ש-Auth Configs ל-Sheets ו-Gmail שניהם עם **Connections: 1** (לא 0) בעמוד Auth Configs ב-Composio Platform. ראי שלבים 15-17 ב-[setup-guide-he.md](setup-guide-he.md).
2. הסקריפט מנסה לגלות אוטומטית את ה-user_id שלך. אם יש לך מספר חשבונות עם חיבורים חלקיים — הגדירי את `COMPOSIO_USER_ID` ידנית. תוכלי למצוא את הערך עם:

```python
from composio import Composio
import os
c = Composio(api_key=os.environ['COMPOSIO_API_KEY'])
for a in c.connected_accounts.list().items:
    print(a.user_id, a.toolkit.slug, a.status)
```

### "Sent message id=None" אבל המייל לא הגיע

זה היה באג ישן בסכמת ה-Gmail (השתמשנו ב-`raw` MIME שלא קיים). תוקן ב-`mailer.py`. ודאי שיש לך את הגרסה האחרונה. אם זה עדיין קורה, תקיני: בדקי שיש לך חיבור Gmail פעיל ב-Composio + שהמשתמש המורשה הוא אותה כתובת שאת רוצה לשלוח ממנה.

### "EMPLOYEE_TABS must be a JSON array string"

בקובץ `.env` חובה לעטוף בגרשיים יחידים את הערך כי הוא מכיל סוגריים מרובעים:

```env
# ❌ לא יעבוד
EMPLOYEE_TABS=["אופיר","אביב"]

# ✓ תקין
EMPLOYEE_TABS='["אופיר","אביב"]'
```

ב-GitHub Secrets לא צריך quotes — מדביקים את ה-JSON בלי גרשיים.

### "ModuleNotFoundError: No module named 'scripts'"

הריצי תמיד `python -m scripts.generate_report`, לא `python scripts/generate_report.py`. אם את מריצה משורש הסקיל, ה-`-m` דואג ש-Python ימצא את החבילה.

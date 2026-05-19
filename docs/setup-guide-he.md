# מדריך התקנה — Weekly Hours Report

מדריך צעד-אחר-צעד למשתתפי הסדנא. אם משהו לא ברור, ראה [troubleshooting.md](troubleshooting.md).

## 1. הרשמה ל-Rube

- כנסי ל-[rube.app](https://rube.app) והרשמי (חינם).
- אחרי ההרשמה, גשי ל-Dashboard ולחצי על "API Keys".
- צרי API key חדש בשם "Claude Code Workshop".
- העתיקי את ה-API key — תצטרכי אותו בהמשך.

(הוסיפו screenshot: `screenshots/01-rube-signup.png`)

## 2. חיבור Rube ל-Claude Code

עקבי אחרי המדריך הרשמי של Rube ב-rube.app/docs/claude-code. בסוף תוודאי ש-Claude מזהה את Rube:

הקלידי בשיחה ל-Claude: `list my Rube connections`. אם Claude מחזיר רשימה (גם אם ריקה) — זה עובד.

(הוסיפו screenshot: `screenshots/02-claude-rube-connected.png`)

## 3. הורדת הסקיל

```bash
git clone https://github.com/YOUR_USERNAME/weekly-hours-report.git ~/.claude/skills/weekly-hours-report
cd ~/.claude/skills/weekly-hours-report
```

## 4. התקנת התלויות

```bash
python -m venv .venv
source .venv/bin/activate   # ב-Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 5. הגדרת ה-API key

```bash
export COMPOSIO_API_KEY="הדבק כאן את המפתח שהעתקת בשלב 1"
```

(ב-zsh/bash הוסיפי את השורה ל-`~/.zshrc` כדי שתישמר).

## 6. הרצת ה-setup

```bash
python scripts/setup.py
```

ה-script יבקש:

- **Google Sheet ID** — מתוך ה-URL של הטבלה. הוא הקטע בין `/d/` ל-`/edit`.
- **שמות טאבים** — בדיוק כמו שהם בטבלה, מופרדים בפסיק.
- **מייל יעד** — מי מקבל את הדוח.
- **Cron** — מתי לשלוח. השאירי את הברירה (`0 8 * * 0`) לראשון 08:00.

חלון דפדפן יפתח פעמיים — פעם ל-Google Sheets ופעם ל-Gmail — לאישור הרשאות OAuth. אשרי בשני המקרים.

(הוסיפו screenshot: `screenshots/03-oauth-flow.png`)

## 7. שליחת דוח test

בסיום ה-setup ה-script ישאל אם לשלוח test. בחרי `y`. תוך 30 שניות אמור להגיע מייל לכתובת שהגדרת. אם לא הגיע — ראי [troubleshooting.md](troubleshooting.md).

## 8. סיום

מעכשיו הדוח יישלח אוטומטית ראשון 08:00. אין צורך לעשות כלום — Rube יריץ את ה-script ב-sandbox שלה.

## להעביר את הסקיל למישהו אחר

כל משתתף בסדנא צריך:
1. חשבון Rube משלו
2. גישה משלו לטבלה (או טבלה משלו)
3. להריץ `setup.py` עם הפרטים שלו

ה-`config.json` הוא אישי ולא נכנס ל-Git, אז אין סכנת דליפת סודות.

"""Interactive setup: validate Composio env, write config.json, optionally send a test report."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "config.json"
EXAMPLE_PATH = SKILL_ROOT / "config.example.json"


def _input(prompt: str, default: str | None = None) -> str:
    if default is not None:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    value = input(prompt).strip()
    if not value and default is not None:
        return default
    return value


def _check_composio_env() -> None:
    if not os.environ.get("COMPOSIO_API_KEY"):
        print("\n❌ משתנה הסביבה COMPOSIO_API_KEY לא מוגדר.")
        print("   1. הירשמי ב-https://composio.dev")
        print("   2. צרי API key.")
        print("   3. הוסיפי לטרמינל: export COMPOSIO_API_KEY=...")
        sys.exit(2)


def _load_template() -> dict:
    with open(EXAMPLE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _prompt_config(template: dict) -> dict:
    cfg = json.loads(json.dumps(template))  # deep copy

    cfg["sheet"]["spreadsheet_id"] = _input("מזהה Google Sheet (Spreadsheet ID)")
    tabs_str = _input("שמות טאבים מופרדים בפסיק (אופיר, אביב, ...)")
    cfg["sheet"]["employee_tabs"] = [t.strip() for t in tabs_str.split(",") if t.strip()]

    cfg["email"]["recipient"] = _input("כתובת מייל ליעד")
    cc_str = _input("עותקים (CC) — מייל אחד או יותר מופרדים בפסיק (Enter לדלג)", default="")
    cfg["email"]["cc"] = [c.strip() for c in cc_str.split(",") if c.strip()] if cc_str else []

    cron = _input("Cron (default ראשון 08:00)", default=cfg["schedule"]["cron"])
    cfg["schedule"]["cron"] = cron
    return cfg


def _write_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"✓ נכתב {CONFIG_PATH}")


def _print_next_steps() -> None:
    print()
    print("✓ config.json נכתב.")
    print()
    print("כדי להריץ דוח מקומי כעת (משורש התיקייה):")
    print("   python -m scripts.generate_report")
    print()
    print("כדי להפעיל cron שבועי, פורקי את הריפו ב-GitHub והוסיפי Repository Secrets:")
    print("   - COMPOSIO_API_KEY")
    print("   - SHEET_ID")
    print("   - EMPLOYEE_TABS  (מחרוזת JSON, למשל [\"אופיר\",\"אביב\"])")
    print("   - RECIPIENT_EMAIL")
    print("   - CC_EMAILS  (אופציונלי, מופרד בפסיק)")
    print("   - COMPOSIO_USER_ID  (אופציונלי — אם לא תוסיפי, יתגלה אוטומטית)")
    print()
    print("הקרון ירוץ ראשון 08:00 שעון ישראל אוטומטית דרך GitHub Actions.")
    print("ראי docs/setup-guide-he.md למדריך מלא עם צילומי מסך.")


def _offer_test_send() -> None:
    ans = _input("\nלשלוח דוח test עכשיו? (y/n)", default="n")
    if ans.lower().startswith("y"):
        import subprocess
        subprocess.run([sys.executable, "-m", "scripts.generate_report"], cwd=str(SKILL_ROOT), check=False)


def main() -> int:
    print("=" * 60)
    print("Weekly Hours Report — Setup (Composio Platform)")
    print("=" * 60)
    _check_composio_env()

    template = _load_template()
    cfg = _prompt_config(template)
    _write_config(cfg)
    _print_next_steps()
    _offer_test_send()

    print("\n✓ סיום! הדוח השבועי יישלח לפי ה-cron שהגדרת (דרך GitHub Actions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

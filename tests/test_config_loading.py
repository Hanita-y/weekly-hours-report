"""Tests for env-var config loading (used by GitHub Actions cron mode)."""
from __future__ import annotations

import json

import pytest

from scripts.generate_report import load_config_from_env


def _set_env(monkeypatch, **kv):
    """Apply a dict of env vars; missing values cleared."""
    for k, v in kv.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)


def test_load_config_from_env_minimal(monkeypatch):
    _set_env(
        monkeypatch,
        COMPOSIO_API_KEY="ck_test",
        SHEET_ID="SHEET_ABC",
        EMPLOYEE_TABS='["אופיר","אביב"]',
        RECIPIENT_EMAIL="boss@example.com",
        CC_EMAILS=None,
        TZ=None,
    )
    cfg = load_config_from_env()
    assert cfg["sheet"]["spreadsheet_id"] == "SHEET_ABC"
    assert cfg["sheet"]["employee_tabs"] == ["אופיר", "אביב"]
    assert cfg["email"]["recipient"] == "boss@example.com"
    assert cfg["email"]["cc"] == []
    assert cfg["schedule"]["timezone"] == "Asia/Jerusalem"
    # Defaults from config.example.json must come through:
    assert "columns" in cfg["sheet"]
    assert "anomaly_thresholds" in cfg
    assert "workdays" in cfg
    assert "branding" in cfg


def test_load_config_from_env_with_cc_and_tz(monkeypatch):
    _set_env(
        monkeypatch,
        COMPOSIO_API_KEY="ck_test",
        SHEET_ID="SHEET_XYZ",
        EMPLOYEE_TABS='["נועה"]',
        RECIPIENT_EMAIL="boss@example.com",
        CC_EMAILS="cc1@example.com, cc2@example.com",
        TZ="UTC",
    )
    cfg = load_config_from_env()
    assert cfg["email"]["cc"] == ["cc1@example.com", "cc2@example.com"]
    assert cfg["schedule"]["timezone"] == "UTC"


def test_load_config_from_env_missing_required(monkeypatch):
    _set_env(
        monkeypatch,
        COMPOSIO_API_KEY="ck_test",
        SHEET_ID=None,
        EMPLOYEE_TABS=None,
        RECIPIENT_EMAIL=None,
    )
    with pytest.raises(RuntimeError) as exc_info:
        load_config_from_env()
    msg = str(exc_info.value)
    assert "SHEET_ID" in msg
    assert "EMPLOYEE_TABS" in msg
    assert "RECIPIENT_EMAIL" in msg


def test_load_config_from_env_bad_tabs_json(monkeypatch):
    _set_env(
        monkeypatch,
        COMPOSIO_API_KEY="ck_test",
        SHEET_ID="SHEET_ABC",
        EMPLOYEE_TABS="not json [",
        RECIPIENT_EMAIL="boss@example.com",
    )
    with pytest.raises(RuntimeError) as exc_info:
        load_config_from_env()
    assert "EMPLOYEE_TABS" in str(exc_info.value)


def test_load_config_from_env_tabs_must_be_list_of_strings(monkeypatch):
    _set_env(
        monkeypatch,
        COMPOSIO_API_KEY="ck_test",
        SHEET_ID="SHEET_ABC",
        EMPLOYEE_TABS=json.dumps({"not": "a list"}),
        RECIPIENT_EMAIL="boss@example.com",
    )
    with pytest.raises(RuntimeError):
        load_config_from_env()

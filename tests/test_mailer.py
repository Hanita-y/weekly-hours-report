"""Tests for mailer.py — Gmail via Composio Platform.

Composio's GMAIL_SEND_EMAIL tool uses structured params (recipient_email/subject/
body/is_html/cc) rather than a raw MIME envelope. PDF attachment is not
implemented yet (Composio S3 upload step needed), so pdf_bytes/pdf_filename
are accepted but ignored by `send_report`.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.mailer import MailerError, send_report


def test_send_report_calls_composio_with_structured_params():
    mock_client = MagicMock()
    mock_client.execute_tool.return_value = {"data": {"id": "msg123"}, "successful": True, "error": None}
    result = send_report(
        composio_client=mock_client,
        sender="me@example.com",
        recipient="boss@example.com",
        cc=["assistant@example.com"],
        subject="Test",
        html="<p>שלום</p>",
        pdf_bytes=b"%PDF stub",
        pdf_filename="weekly.pdf",
    )
    assert result["data"]["id"] == "msg123"
    args, _ = mock_client.execute_tool.call_args
    assert args[0] == "GMAIL_SEND_EMAIL"
    params = args[1]
    assert params["recipient_email"] == "boss@example.com"
    assert params["subject"] == "Test"
    assert params["body"] == "<p>שלום</p>"
    assert params["is_html"] is True
    assert params["cc"] == ["assistant@example.com"]


def test_send_report_omits_cc_when_empty():
    mock_client = MagicMock()
    mock_client.execute_tool.return_value = {"data": {"id": "x"}}
    send_report(
        composio_client=mock_client,
        sender="me@x.com", recipient="boss@x.com", cc=[],
        subject="S", html="b", pdf_bytes=b"", pdf_filename="x.pdf",
    )
    args, _ = mock_client.execute_tool.call_args
    params = args[1]
    assert "cc" not in params


def test_send_report_retries_on_failure():
    mock_client = MagicMock()
    mock_client.execute_tool.side_effect = [
        Exception("transient"),
        Exception("transient"),
        {"data": {"id": "msg_after_retry"}},
    ]
    result = send_report(
        composio_client=mock_client,
        sender="me@example.com",
        recipient="boss@example.com",
        cc=[],
        subject="Subject",
        html="<p>body</p>",
        pdf_bytes=b"%PDF stub",
        pdf_filename="weekly.pdf",
        max_retries=3,
    )
    assert result["data"]["id"] == "msg_after_retry"
    assert mock_client.execute_tool.call_count == 3


def test_send_report_raises_after_max_retries():
    mock_client = MagicMock()
    mock_client.execute_tool.side_effect = Exception("permanent")
    with pytest.raises(MailerError) as exc_info:
        send_report(
            composio_client=mock_client,
            sender="me@example.com",
            recipient="boss@example.com",
            cc=[],
            subject="Subject",
            html="<p>body</p>",
            pdf_bytes=b"%PDF stub",
            pdf_filename="weekly.pdf",
            max_retries=2,
        )
    assert "permanent" in str(exc_info.value)
    assert mock_client.execute_tool.call_count == 2

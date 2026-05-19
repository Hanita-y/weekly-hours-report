"""Tests for mailer.py — Gmail via Rube."""
from __future__ import annotations

import base64
from unittest.mock import MagicMock

import pytest

from scripts.mailer import MailerError, build_mime_message, send_report


def test_build_mime_message_has_html_and_attachment():
    raw = build_mime_message(
        sender="me@example.com",
        recipient="boss@example.com",
        cc=[],
        subject="Test",
        html="<p>hello</p>",
        pdf_bytes=b"%PDF-1.4 stub",
        pdf_filename="report.pdf",
    )
    decoded = base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8", errors="replace")
    assert "To: boss@example.com" in decoded
    assert "Subject: " in decoded
    assert "Content-Type: text/html" in decoded
    assert "Content-Type: application/pdf" in decoded
    assert "report.pdf" in decoded


def test_build_mime_message_supports_cc():
    raw = build_mime_message(
        sender="me@example.com",
        recipient="boss@example.com",
        cc=["assistant@example.com"],
        subject="Test",
        html="<p>hello</p>",
        pdf_bytes=b"%PDF-1.4 stub",
        pdf_filename="report.pdf",
    )
    decoded = base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8", errors="replace")
    assert "Cc: assistant@example.com" in decoded


def test_send_report_calls_rube():
    mock_client = MagicMock()
    mock_client.execute_tool.return_value = {"id": "msg123", "labelIds": ["SENT"]}
    result = send_report(
        rube_client=mock_client,
        sender="me@example.com",
        recipient="boss@example.com",
        cc=[],
        subject="Subject",
        html="<p>body</p>",
        pdf_bytes=b"%PDF stub",
        pdf_filename="weekly.pdf",
    )
    assert result["id"] == "msg123"
    args, kwargs = mock_client.execute_tool.call_args
    assert args[0] == "GMAIL_SEND_EMAIL"
    params = args[1]
    assert "raw" in params


def test_send_report_retries_on_failure():
    mock_client = MagicMock()
    mock_client.execute_tool.side_effect = [
        Exception("transient"),
        Exception("transient"),
        {"id": "msg_after_retry"},
    ]
    result = send_report(
        rube_client=mock_client,
        sender="me@example.com",
        recipient="boss@example.com",
        cc=[],
        subject="Subject",
        html="<p>body</p>",
        pdf_bytes=b"%PDF stub",
        pdf_filename="weekly.pdf",
        max_retries=3,
    )
    assert result["id"] == "msg_after_retry"
    assert mock_client.execute_tool.call_count == 3


def test_send_report_raises_after_max_retries():
    mock_client = MagicMock()
    mock_client.execute_tool.side_effect = Exception("permanent")
    with pytest.raises(MailerError) as exc_info:
        send_report(
            rube_client=mock_client,
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

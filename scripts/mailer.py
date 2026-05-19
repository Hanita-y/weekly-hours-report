"""Send the rendered report via Gmail through the Composio Platform.

Composio's GMAIL_SEND_EMAIL tool uses structured params (recipient_email, subject,
body, is_html, cc) rather than a raw MIME envelope. PDF attachments require a
separate upload step to Composio's storage — not implemented here yet; the
HTML body already contains the full report.
"""
from __future__ import annotations

import time
from typing import Any


class MailerError(Exception):
    """Raised when Gmail send fails after retries."""


def send_report(
    composio_client: Any,
    sender: str,
    recipient: str,
    cc: list[str],
    subject: str,
    html: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Send the report through the Composio Gmail tool with retries on transient failure.

    Note: pdf_bytes / pdf_filename are accepted for interface stability but currently
    not attached. Composio's Gmail tool requires attachments uploaded via S3 first.
    The HTML body contains the full report, so PDF is supplementary.
    """
    params: dict[str, Any] = {
        "recipient_email": recipient,
        "subject": subject,
        "body": html,
        "is_html": True,
    }
    if cc:
        params["cc"] = cc

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return composio_client.execute_tool("GMAIL_SEND_EMAIL", params)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise MailerError(f"Failed to send Gmail after {max_retries} attempts: {last_error}")

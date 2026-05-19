"""Send the rendered report via Gmail through Rube/Composio."""
from __future__ import annotations

import base64
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any


class MailerError(Exception):
    """Raised when Gmail send fails after retries."""


def build_mime_message(
    sender: str,
    recipient: str,
    cc: list[str],
    subject: str,
    html: str,
    pdf_bytes: bytes,
    pdf_filename: str,
) -> str:
    """Build an RFC 2822 multipart message and return it base64url-encoded for Gmail API."""
    msg = MIMEMultipart("mixed")
    msg["To"] = recipient
    msg["From"] = sender
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = ", ".join(cc)

    msg.attach(MIMEText(html, "html", "utf-8"))

    attachment = MIMEBase("application", "pdf")
    attachment.set_payload(pdf_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    raw_bytes = msg.as_bytes()
    return base64.urlsafe_b64encode(raw_bytes).decode("ascii")


def send_report(
    rube_client: Any,
    sender: str,
    recipient: str,
    cc: list[str],
    subject: str,
    html: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Send the report through Rube's Gmail tool with retries on transient failure."""
    raw = build_mime_message(sender, recipient, cc, subject, html, pdf_bytes, pdf_filename)

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return rube_client.execute_tool("GMAIL_SEND_EMAIL", {"raw": raw})
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise MailerError(f"Failed to send Gmail after {max_retries} attempts: {last_error}")

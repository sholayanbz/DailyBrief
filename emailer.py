#!/usr/bin/env python3
"""
emailer.py — HTML Email Sender via SendGrid (Railway edition)
Matches the EmailSender pattern from the watchlist scanner project.

Required env vars:
  SENDGRID_API_KEY  — your SendGrid API key
  FROM_EMAIL        — verified sender address (same as scanner project)
  EMAIL_TO          — comma-separated recipients, e.g. sharif@gmail.com
                      OR create an emails.txt file with one address per line
"""

import base64
import os
import sys
from datetime import date
from pathlib import Path

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition
)


def _load_recipients() -> list[str]:
    """Load recipients from EMAIL_TO env var or emails.txt (same as scanner project)."""
    # Check env var first
    env_to = os.environ.get("EMAIL_TO", "")
    if env_to:
        return [e.strip() for e in env_to.split(",") if e.strip()]

    # Fall back to emails.txt in the working directory
    emails_file = Path("emails.txt")
    if emails_file.exists():
        emails = []
        with open(emails_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "@" in line:
                    emails.append(line)
        return emails

    raise RuntimeError("No recipients configured. Set EMAIL_TO or create emails.txt.")


def run(html_path: str, subject: str | None = None, attach_file: str | None = None) -> bool:
    """
    Send the brief HTML as an email via SendGrid.

    Args:
        html_path:   Path to the generated HTML brief (sent as email body).
        subject:     Email subject — auto-generated if None.
        attach_file: Optional path to attach (e.g. same HTML for download).

    Returns:
        True if all recipients succeeded, False otherwise.
    """
    api_key    = os.environ["SENDGRID_API_KEY"]
    from_email = os.environ["FROM_EMAIL"]
    recipients = _load_recipients()

    today   = date.today().strftime("%B %-d, %Y")
    subject = subject or f"Daily Brief — {today}"

    with open(html_path, "r", encoding="utf-8") as f:
        html_body = f.read()

    sg = SendGridAPIClient(api_key)
    all_ok = True

    for recipient in recipients:
        message = Mail(
            from_email=from_email,
            to_emails=recipient,
            subject=subject,
            html_content=html_body,
        )

        # Optional attachment (e.g. attach the same HTML for offline viewing)
        if attach_file and Path(attach_file).exists():
            try:
                with open(attach_file, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                message.attachment = Attachment(
                    FileContent(encoded),
                    FileName(Path(attach_file).name),
                    FileType("text/html"),
                    Disposition("attachment"),
                )
                print(f"[emailer] Attached {Path(attach_file).name}")
            except Exception as e:
                print(f"[emailer] Warning: could not attach file — {e}")

        response = sg.send(message)

        if 200 <= response.status_code < 300:
            print(f"[emailer] ✅ Sent '{subject}' → {recipient} (status {response.status_code})")
        else:
            print(f"[emailer] ❌ SendGrid error for {recipient}: {response.status_code} {response.body}")
            all_ok = False

    return all_ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 emailer.py path/to/brief.html")
        sys.exit(1)
    ok = run(sys.argv[1])
    sys.exit(0 if ok else 1)

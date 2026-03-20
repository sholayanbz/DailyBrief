#!/usr/bin/env python3
"""
emailer.py — HTML Email Sender via SMTP

Required env vars:
  SMTP_USER      — sender address (e.g. sharif.olayan@gmail.com)
  SMTP_PASSWORD  — app password
  SMTP_HOST      — e.g. smtp.gmail.com (default)
  SMTP_PORT      — e.g. 465 (SSL) or 587 (TLS)
  FROM_EMAIL     — sender display address (falls back to SMTP_USER)
  EMAIL_TO       — comma-separated recipients
                   OR create an emails.txt file with one address per line
"""

import os
import smtplib
import ssl
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def _load_recipients() -> list[str]:
    env_to = os.environ.get("EMAIL_TO", "")
    if env_to:
        return [e.strip() for e in env_to.split(",") if e.strip()]

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
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASSWORD"]
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    from_email = os.environ.get("FROM_EMAIL", smtp_user)
    recipients = _load_recipients()

    today = date.today().strftime("%B %-d, %Y")
    subject = subject or f"Daily Brief — {today}"

    with open(html_path, "r", encoding="utf-8") as f:
        html_body = f.read()

    use_ssl = smtp_port == 465

    all_ok = True
    for recipient in recipients:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))

        try:
            if use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(from_email, recipient, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls(context=ssl.create_default_context())
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(from_email, recipient, msg.as_string())

            print(f"[emailer] ✅ Sent '{subject}' → {recipient}")
        except Exception as e:
            print(f"[emailer] ❌ Failed to send to {recipient}: {e}")
            all_ok = False

    return all_ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 emailer.py path/to/brief.html")
        sys.exit(1)
    ok = run(sys.argv[1])
    sys.exit(0 if ok else 1)

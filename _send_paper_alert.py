"""Send the latest Hydrogeochem Paper Alert digest via Gmail SMTP.

Environment variables:
  TODAY               YYYY-MM-DD (optional; defaults to the newest digest file)
  GMAIL_USERNAME      Sender Gmail address
  GMAIL_APP_PASSWORD  16-char Gmail App Password (2FA must be enabled)
  MAIL_TO             Comma-separated recipient list
  MAIL_SUBJECT        Optional subject override

Reads paper_alert/digests/paper_alert_<TODAY>.html and sends it as the
HTML body of a multipart/alternative message. Stdlib only.
"""

from __future__ import annotations

import os
import re
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

DIGEST_DIR = Path("paper_alert/digests")


def kst_today() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%Y-%m-%d")


def resolve_digest() -> Path | None:
    today = os.environ.get("TODAY", "").strip()
    if today:
        candidate = DIGEST_DIR / f"paper_alert_{today}.html"
        return candidate if candidate.is_file() else None
    found = sorted(DIGEST_DIR.glob("paper_alert_*.html"))
    return found[-1] if found else None


def main() -> int:
    user = os.environ.get("GMAIL_USERNAME", "").strip()
    pwd = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    raw_to = os.environ.get("MAIL_TO", "").strip()

    missing = [
        name
        for name, value in (
            ("GMAIL_USERNAME", user),
            ("GMAIL_APP_PASSWORD", pwd),
            ("MAIL_TO", raw_to),
        )
        if not value
    ]
    if missing:
        print(f"::error::Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        return 2

    recipients = [addr.strip() for addr in raw_to.split(",") if addr.strip()]
    if not recipients:
        print("::error::MAIL_TO has no valid recipients", file=sys.stderr)
        return 2

    digest = resolve_digest()
    if digest is None:
        print(
            "::error::No paper-alert digest HTML found in paper_alert/digests/",
            file=sys.stderr,
        )
        return 1

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", digest.name)
    date_str = date_match.group(1) if date_match else kst_today()

    html_body = digest.read_text(encoding="utf-8")
    subject = os.environ.get("MAIL_SUBJECT") or f"[Hydrogeochem Paper Alert] {date_str}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg.set_content(
        f"Hydrogeochem Paper Alert digest for {date_str}.\n"
        "Open this message in an HTML-capable mail client to read the digest.\n"
    )
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)

    print(f"Sent paper alert digest ({digest.name}) to {len(recipients)} recipient(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

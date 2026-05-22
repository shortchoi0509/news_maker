"""Send the day's daily brief HTML to recipients via Gmail SMTP.

Environment variables:
  TODAY               YYYY-MM-DD (defaults to today's date in KST)
  GMAIL_USERNAME      Sender Gmail address
  GMAIL_APP_PASSWORD  16-char Gmail App Password (2FA must be enabled)
  MAIL_TO             Comma-separated recipient list
  MAIL_SUBJECT        Optional subject override

Reads out/<TODAY>/html/daily_brief_<TODAY>.html and sends it as the
HTML body of a multipart/alternative message.
"""

from __future__ import annotations

import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path


def kst_today() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%Y-%m-%d")


def main() -> int:
    today = os.environ.get("TODAY") or kst_today()
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

    email_html = Path(f"out/{today}/html/email_brief_{today}.html")
    full_html = Path(f"out/{today}/html/daily_brief_{today}.html")
    if email_html.is_file():
        html_path = email_html
    elif full_html.is_file():
        print(
            "::warning::email_brief not found, falling back to full daily_brief",
            file=sys.stderr,
        )
        html_path = full_html
    else:
        print(
            f"::error::No HTML brief found: {email_html} / {full_html}",
            file=sys.stderr,
        )
        return 1

    html_body = html_path.read_text(encoding="utf-8")
    subject = os.environ.get("MAIL_SUBJECT") or f"[데일리 브리프] {today} 매일경제 핵심 뉴스"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg.set_content(
        f"오늘({today})의 매일경제 데일리 브리프입니다.\n"
        "HTML을 지원하는 메일 클라이언트에서 본문을 확인하시거나,\n"
        f"첨부된 {html_path.name} 파일을 브라우저로 열어보세요.\n"
    )
    msg.add_alternative(html_body, subtype="html")
    msg.add_attachment(
        html_body.encode("utf-8"),
        maintype="application",
        subtype="octet-stream",
        filename=html_path.name,
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)

    print(f"Sent daily brief for {today} to {len(recipients)} recipient(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Sends the Zoom link email to all confirmed course registrants.

Usage (run manually 1 week before each course date):
  /var/www/magicspace/venv/bin/python3 /var/www/magicspace/scripts/send_kurz_link.py \
    --date "4. júla 2025" \
    --zoom "https://zoom.us/j/XXXXXXXXX"

Or set env vars KURZ_DATE and ZOOM_URL and run without args.
"""

import sys, os, sqlite3, smtplib, logging, argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
load_dotenv(os.path.join(BASE, ".env"))

DB          = os.path.join(BASE, "magicspace.db")
MAIL_USER   = os.getenv("MAIL_USER", "")
MAIL_PASS   = os.getenv("MAIL_PASS", "")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.forpsi.com")
MAIL_PORT   = int(os.getenv("MAIL_PORT", "465"))
SITE_URL    = os.getenv("SITE_URL", "https://magicspace.sk")

TEMPLATE = os.path.join(BASE, "content", "sk", "emails", "kurz_link.html")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)


def send_one(to_email, subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = MAIL_USER
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as s:
        s.login(MAIL_USER, MAIL_PASS)
        s.sendmail(MAIL_USER, [to_email], msg.as_string())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=os.getenv("KURZ_DATE", ""), help="Dátum kurzu, napr. '4. júla 2025'")
    parser.add_argument("--zoom", default=os.getenv("ZOOM_URL", ""), help="Zoom odkaz")
    parser.add_argument("--dry-run", action="store_true", help="Iba vypíš emaily, neposiela")
    args = parser.parse_args()

    if not args.date or not args.zoom:
        print("ERROR: Zadaj --date a --zoom")
        print("Príklad: python3 send_kurz_link.py --date '4. júla 2025' --zoom 'https://zoom.us/j/...'")
        sys.exit(1)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT email FROM subscribers WHERE kurz_confirmed = 1 AND unsubscribed = 0"
    ).fetchall()
    conn.close()

    if not rows:
        log.info("Žiadni potvrdení účastníci v databáze.")
        return

    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()

    subject = f"Odkaz na kurz – {args.date}"
    sent = 0
    for row in rows:
        email = row["email"]
        html = tpl.replace("{{kurz_date}}", args.date)
        html = html.replace("{{zoom_url}}", args.zoom)
        if args.dry_run:
            log.info(f"DRY-RUN → {email}")
            continue
        try:
            send_one(email, subject, html)
            log.info(f"OK → {email}")
            sent += 1
        except Exception as e:
            log.error(f"ERR → {email}: {e}")

    log.info(f"Done. Sent: {sent} / {len(rows)}")


if __name__ == "__main__":
    main()

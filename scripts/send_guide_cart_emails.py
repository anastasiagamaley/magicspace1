#!/usr/bin/env python3
"""
Abandoned-cart email for partner guide (€15 PDF).

Sends nurture_guide_cart.html to subscribers who:
  - clicked the guide buy link (guide_interest_at is set)
  - at least 24 hours ago
  - haven't unsubscribed
  - haven't received this cart email yet (guide_cart_sent = 0)

Cron (on server):
  30 10 * * * /var/www/magicspace/venv/bin/python3 /var/www/magicspace/scripts/send_guide_cart_emails.py >> /var/www/magicspace/logs/nurture.log 2>&1
"""

import sys, os, sqlite3, smtplib, logging, base64
from datetime import datetime, timedelta
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

SUBJECT  = "Možno ťa niečo zdržalo"
TEMPLATE = os.path.join(BASE, "content", "sk", "emails", "nurture_guide_cart.html")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)


def tracked_url(email, path):
    token = base64.urlsafe_b64encode(email.encode()).rstrip(b"=").decode()
    return f"{SITE_URL}/{path}?e={token}"


def send_one(to_email, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"]    = MAIL_USER
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as s:
        s.login(MAIL_USER, MAIL_PASS)
        s.sendmail(MAIL_USER, [to_email], msg.as_string())


def main():
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """SELECT id, email, guide_interest_at FROM subscribers
           WHERE unsubscribed = 0
             AND guide_cart_sent = 0
             AND guide_interest_at != ''
             AND guide_interest_at IS NOT NULL
             AND guide_interest_at <= ?""",
        (cutoff,)
    ).fetchall()

    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()

    sent = 0
    for row in rows:
        email = row["email"]
        html = tpl.replace("{{unsubscribe_url}}", f"{SITE_URL}/unsubscribe?email={email}")
        html = html.replace("{{guide_url}}", tracked_url(email, "go/partner-guide"))
        try:
            send_one(email, html)
            cur.execute("UPDATE subscribers SET guide_cart_sent=1 WHERE id=?", (row["id"],))
            conn.commit()
            log.info(f"OK guide_cart → {email}")
            sent += 1
        except Exception as e:
            log.error(f"ERR guide_cart → {email}: {e}")

    conn.close()
    log.info(f"Done. Sent: {sent}")


if __name__ == "__main__":
    main()

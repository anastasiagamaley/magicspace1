#!/usr/bin/env python3
"""
Nurture sequence sender — run daily by cron at 09:00.

Cron (on server):
  0 9 * * * /usr/bin/python3 /var/www/magicspace/scripts/send_nurture.py >> /var/www/magicspace/logs/nurture.log 2>&1

Schedule (days after signup):
  step 2 → day 3
  step 3 → day 6
  step 4 → day 9
  step 5 → day 12
  step 6 → day 16
"""

import sys, os, sqlite3, smtplib, logging, base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
load_dotenv(os.path.join(BASE, ".env"))

DB         = os.path.join(BASE, "magicspace.db")
MAIL_USER  = os.getenv("MAIL_USER", "")
MAIL_PASS  = os.getenv("MAIL_PASS", "")
MAIL_SERVER= os.getenv("MAIL_SERVER", "smtp.forpsi.com")
MAIL_PORT  = int(os.getenv("MAIL_PORT", "465"))
SITE_URL   = os.getenv("SITE_URL", "https://magicspace.sk")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

# step → (subject, template_file)
STEPS = {
    2: ("3 veci, ktoré by mal vedieť každý partner",       "nurture_2.html"),
    3: ("Rozšírený sprievodca pre partnera",               "nurture_3.html"),
    4: ("Niečo, čo som pripravila práve pre vás",          "nurture_4.html"),
    5: ("Ako vyzerá ten jeden deň",                        "nurture_5.html"),
    6: ("Posledná pripomienka – 4. júla",                  "nurture_6.html"),
}

# days after signup to send each step
STEP_DAY = {2: 3, 3: 6, 4: 9, 5: 12, 6: 16}


def tracked_url(email, path):
    token = base64.urlsafe_b64encode(email.encode()).rstrip(b"=").decode()
    return f"{SITE_URL}/{path}?e={token}"


def load_template(filename, unsubscribe_url, email=""):
    tpl_path = os.path.join(BASE, "content", "sk", "emails", filename)
    with open(tpl_path, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{unsubscribe_url}}", unsubscribe_url)
    html = html.replace("{{kurz_url}}",  tracked_url(email, "go/kurz")          if email else f"{SITE_URL}/kurz.html")
    html = html.replace("{{guide_url}}", tracked_url(email, "go/partner-guide") if email else "https://pay.sumup.com/b2c/QC3SD8JE")
    return html


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
    now = datetime.utcnow()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT id, email, nurture_step, created_at FROM subscribers "
        "WHERE unsubscribed=0 AND nurture_step <= 6"
    ).fetchall()

    sent = 0
    for row in rows:
        step      = row["nurture_step"]
        if step not in STEPS:
            # mark done
            cur.execute("UPDATE subscribers SET nurture_step=7 WHERE id=?", (row["id"],))
            continue

        created   = datetime.fromisoformat(row["created_at"])
        send_on_day = STEP_DAY[step]
        due       = created.replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        due = due + timedelta(days=send_on_day)

        if now < due:
            continue  # not time yet

        subject, tpl = STEPS[step]
        unsubscribe_url = f"{SITE_URL}/unsubscribe?email={row['email']}"
        try:
            html = load_template(tpl, unsubscribe_url, row["email"])
            send_one(row["email"], subject, html)
            cur.execute(
                "UPDATE subscribers SET nurture_step=? WHERE id=?",
                (step + 1, row["id"])
            )
            conn.commit()
            log.info(f"OK step={step} → {row['email']}")
            sent += 1
        except Exception as e:
            log.error(f"ERR step={step} → {row['email']}: {e}")

    conn.close()
    log.info(f"Done. Sent: {sent}")


if __name__ == "__main__":
    main()

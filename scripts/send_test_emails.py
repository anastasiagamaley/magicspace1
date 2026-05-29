#!/usr/bin/env python3
import sys, os, smtplib, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MAIL_USER   = os.getenv("MAIL_USER", "")
MAIL_PASS   = os.getenv("MAIL_PASS", "")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.forpsi.com")
MAIL_PORT   = int(os.getenv("MAIL_PORT", "465"))
SITE_URL    = os.getenv("SITE_URL", "https://magicspace.sk")
BASE        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TO          = "gamaley91@gmail.com"

STEPS = [
    (1, "Vas sprievodca ku porodu – MagicSpace",             "nurture_1.html"),
    (2, "3 veci, ktore by mal vediet kazdy partner",          "nurture_2.html"),
    (3, "Rozsireny sprievodca pre partnera",                  "nurture_3.html"),
    (4, "Nieco, co som pripravila prave pre vas",             "nurture_4.html"),
    (5, "Ako vyzera ten jeden den",                           "nurture_5.html"),
    (6, "Posledna pripomienka – 4. julia",                   "nurture_6.html"),
]

for step, subject, tpl in STEPS:
    path = os.path.join(BASE, "content", "sk", "emails", tpl)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{unsubscribe_url}}", f"{SITE_URL}/unsubscribe?email={TO}")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[TEST {step}/6] {subject}"
    msg["From"]    = MAIL_USER
    msg["To"]      = TO
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as s:
            s.login(MAIL_USER, MAIL_PASS)
            s.sendmail(MAIL_USER, [TO], msg.as_string())
        print(f"OK {step}/6: {tpl}")
    except Exception as e:
        print(f"ERR {step}/6: {e}")
    time.sleep(4)

print("Hotovo!")

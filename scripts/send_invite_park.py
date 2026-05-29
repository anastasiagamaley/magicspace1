#!/usr/bin/env python3
"""
Разовая рассылка приглашения на йогу в парке.
Отправляет по 1 письму в минуту — не триггерит спам-фильтры Gmail.

Использование:
  python scripts/send_invite_park.py

Остановить: Ctrl+C  (прогресс сохранён в send_log.txt, при перезапуске
пропускает уже отправленные адреса)
"""
import sys, os, csv, smtplib, time, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT       = Path(__file__).parent.parent
ENV_FILE   = ROOT / ".env"
EMAIL_HTML = ROOT / "content/sk/emails/invite_park.html"
CSV_FILE   = Path(__file__).parent / "contacts.csv"
LOG_FILE   = Path(__file__).parent / "send_log.txt"

DELAY_SECONDS = 60   # пауза между письмами

# ─── .env ─────────────────────────────────────────────────────
def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

# ─── CSV ──────────────────────────────────────────────────────
def load_contacts():
    contacts = []
    seen = set()
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            email = row.get("Email 1", "").strip().lower()
            if not email or "@" not in email:
                continue
            if email in seen:
                continue
            seen.add(email)
            first = row.get("First Name", "").strip()
            contacts.append({"email": email, "name": first})
    return contacts

# ─── Уже отправленные (из лога) ───────────────────────────────
def load_sent():
    sent = set()
    if LOG_FILE.exists():
        for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("OK "):
                sent.add(line[3:].strip())
    return sent

def append_log(line):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ─── Отправка ─────────────────────────────────────────────────
def send_one(server, mail_user, to_email, html, subject):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Magic Space <{mail_user}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))
    server.sendmail(mail_user, [to_email], msg.as_string())

# ─── Main ─────────────────────────────────────────────────────
def main():
    env = load_env()
    mail_user   = env.get("MAIL_USER") or env.get("GMAIL_USER", "")
    mail_pass   = env.get("MAIL_PASS") or env.get("GMAIL_PASS", "")
    mail_server = env.get("MAIL_SERVER", "smtp.gmail.com")
    mail_port   = int(env.get("MAIL_PORT", "465"))

    if not mail_user or not mail_pass:
        print("❌ Chýba MAIL_USER / MAIL_PASS v .env")
        sys.exit(1)

    contacts = load_contacts()
    already_sent = load_sent()

    todo = [c for c in contacts if c["email"] not in already_sent]

    print(f"📋 Kontaktov celkom:    {len(contacts)}")
    print(f"✅ Už odoslaných:       {len(already_sent)}")
    print(f"📨 Zostáva odoslať:     {len(todo)}")
    print(f"⏱  Pauza medzi mailmi:  {DELAY_SECONDS}s (~{len(todo) * DELAY_SECONDS // 60} min celkom)")
    print(f"📧 Účet:                {mail_user}")
    print()

    if not todo:
        print("Všetko odoslané!")
        return

    if "--yes" not in sys.argv:
        confirm = input(f"Spustiť odosielanie {len(todo)} e-mailov? (ano/nie): ").strip().lower()
        if confirm not in ("ano", "áno", "yes", "y", "a"):
            print("Zrušené.")
            return

    subject  = "Joga v parku – 2. rok · Martin 🌿"
    html_body = EMAIL_HTML.read_text(encoding="utf-8")

    append_log(f"\n=== Start: {time.strftime('%Y-%m-%d %H:%M')} | Zostatok: {len(todo)} ===")

    print(f"\nPripájam sa…")
    try:
        with smtplib.SMTP_SSL(mail_server, mail_port) as server:
            server.login(mail_user, mail_pass)
            print(f"✓ Prihlásený\n")

            for i, contact in enumerate(todo, 1):
                try:
                    send_one(server, mail_user, contact["email"], html_body, subject)
                    append_log(f"OK {contact['email']}")
                    print(f"  [{i}/{len(todo)}] ✓  {contact['email']}")
                except Exception as e:
                    append_log(f"ERR {contact['email']} — {e}")
                    print(f"  [{i}/{len(todo)}] ✗  {contact['email']} — {e}")

                if i < len(todo):
                    print(f"         čakám {DELAY_SECONDS}s…", end="\r")
                    time.sleep(DELAY_SECONDS)

    except KeyboardInterrupt:
        print("\n\nPrerušené. Pri ďalšom spustení preskočí už odoslané.")
    except Exception as e:
        print(f"\n❌ Chyba pripojenia: {e}")

    sent_now = len(load_sent()) - len(already_sent)
    print(f"\n{'='*50}")
    print(f"Odoslané v tejto relácii: {sent_now}")
    print(f"Log: {LOG_FILE}")

if __name__ == "__main__":
    main()

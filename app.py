"""
MagicSpace – Flask backend
Spustite:  python app.py
Otvorte:   http://localhost:5000
"""

from flask import Flask, jsonify, request, send_from_directory, abort, redirect
import sqlite3, os, json, smtplib, threading, base64, secrets
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import atexit
from services.telegram import create_invite_link, handle_update

BASE    = os.path.dirname(os.path.abspath(__file__))
DB      = os.path.join(BASE, "magicspace.db")
UPLOADS = os.path.join(BASE, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

# Načítať .env súbor
load_dotenv(os.path.join(BASE, ".env"))

app = Flask(__name__, static_folder=BASE, static_url_path="")

# ════════════════════════════════════════════════════════════════
# NASTAVENIA – upravujte v súbore .env, nie tu!
# ════════════════════════════════════════════════════════════════
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "")
MAIL_USER      = os.getenv("MAIL_USER",      os.getenv("GMAIL_USER", ""))
MAIL_PASS      = os.getenv("MAIL_PASS",      os.getenv("GMAIL_PASS", ""))
MAIL_SERVER    = os.getenv("MAIL_SERVER",    "smtp.gmail.com")
MAIL_PORT      = int(os.getenv("MAIL_PORT",  "465"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SITE_URL       = os.getenv("SITE_URL",       "http://localhost:5000")
# ════════════════════════════════════════════════════════════════

# ─── DATABÁZA ────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            date        TEXT NOT NULL,
            time        TEXT NOT NULL,
            duration    TEXT DEFAULT '60 min',
            spots       INTEGER DEFAULT 10,
            booked      INTEGER DEFAULT 0,
            price       TEXT DEFAULT '0 €',
            desc        TEXT DEFAULT '',
            location    TEXT DEFAULT 'Andreja Kmeťa 577/22, Martin',
            badge       TEXT DEFAULT 'active',
            project     TEXT DEFAULT 'main',
            image_url   TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER,
            name            TEXT NOT NULL,
            email           TEXT NOT NULL,
            phone           TEXT,
            note            TEXT,
            status          TEXT DEFAULT 'pending',
            reminded        INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            page       TEXT NOT NULL,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL,
            stars      INTEGER DEFAULT 5,
            text       TEXT NOT NULL,
            status     TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL,
            phone      TEXT,
            topic      TEXT,
            message    TEXT,
            status     TEXT DEFAULT 'new',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS subscribers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL UNIQUE,
            due_date   TEXT DEFAULT '',
            consent_at TEXT DEFAULT (datetime('now')),
            source     TEXT DEFAULT 'landing',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS purchases (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL,
            product    TEXT NOT NULL,
            status     TEXT DEFAULT 'pending',
            token      TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)

        # Pridať stĺpce ak ešte neexistujú (pre existujúce DB)
        for col_sql in [
            "ALTER TABLE sessions ADD COLUMN image_url TEXT DEFAULT ''",
            "ALTER TABLE sessions ADD COLUMN recur_type TEXT DEFAULT ''",
            "ALTER TABLE sessions ADD COLUMN recur_until TEXT DEFAULT ''",
            "ALTER TABLE sessions ADD COLUMN recur_parent_id INTEGER DEFAULT NULL",
            "ALTER TABLE bookings ADD COLUMN reminded INTEGER DEFAULT 0",
            "ALTER TABLE bookings ADD COLUMN terms_accepted INTEGER DEFAULT 0",
            "ALTER TABLE subscribers ADD COLUMN nurture_step INTEGER DEFAULT 1",
            "ALTER TABLE subscribers ADD COLUMN next_nurture_at TEXT DEFAULT ''",
            "ALTER TABLE subscribers ADD COLUMN unsubscribed INTEGER DEFAULT 0",
            "ALTER TABLE subscribers ADD COLUMN kurz_interest_at TEXT DEFAULT ''",
            "ALTER TABLE subscribers ADD COLUMN cart_email_sent INTEGER DEFAULT 0",
            "ALTER TABLE subscribers ADD COLUMN guide_interest_at TEXT DEFAULT ''",
            "ALTER TABLE subscribers ADD COLUMN guide_cart_sent INTEGER DEFAULT 0",
            "ALTER TABLE subscribers ADD COLUMN bundle_cart_sent INTEGER DEFAULT 0",
            "ALTER TABLE subscribers ADD COLUMN cart_all_sent INTEGER DEFAULT 0",
            "ALTER TABLE subscribers ADD COLUMN kurz_confirmed INTEGER DEFAULT 0",
        ]:
            try:
                db.execute(col_sql)
                db.commit()
            except:
                pass

        # Ukážkové sésie
        count = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        if count == 0:
            db.executemany("""
                INSERT INTO sessions (title,date,time,duration,spots,booked,price,desc,location,badge,project)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, [
                ("Sound Healing","2025-06-07","18:00","90 min",10,6,"20 €",
                 "Hlboká relaxácia s tibetskými spievajúcimi miskami.",
                 "Andreja Kmeťa 577/22, Martin","active","main"),
                ("Joga pre tehotné","2025-06-11","17:30","75 min",8,3,"12 €",
                 "Jemná joga pre tehotné ženy. Streda 17:30.",
                 "Andreja Kmeťa 577/22, Martin","active","main"),
                ("Intuitívny tanec","2025-06-14","17:00","90 min",15,5,"15 €",
                 "Meditácia v pohybe, kde sa stretávaš sám so sebou.",
                 "Andreja Kmeťa 577/22, Martin","active","main"),
                ("Ranná joga v parku","2025-06-04","07:00","60 min",20,8,"8 €",
                 "Ideálny začiatok dňa. Ráno v parku, čerstvý vzduch.",
                 "Schody pred Múzeom, Martin","active","park"),
                ("Večerná joga v parku","2025-06-04","18:00","60 min",20,12,"8 €",
                 "Uzavrite pracovný deň pohybom v prírode.",
                 "Schody pred Múzeom, Martin","active","park"),
            ])
            db.commit()

# ─── EMAIL ───────────────────────────────────────────────────
def send_email(to_list, subject, html_body):
    """Odošle email na zoznam adresátov. Spustí sa vo vlákne aby neblokoval server."""
    def _send():
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"MagicSpace <{MAIL_USER}>"
            msg["To"]      = ", ".join(to_list)
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as server:
                server.login(MAIL_USER, MAIL_PASS)
                server.sendmail(MAIL_USER, to_list, msg.as_string())
            print(f"✉️  Email odoslaný: {subject} → {to_list}")
        except Exception as e:
            print(f"❌  Email chyba: {e}")
            print("    Skontrolujte GMAIL_USER a GMAIL_PASS v app.py")

    threading.Thread(target=_send, daemon=True).start()

def email_booking_client(booking, session):
    """Email klientovi po rezervácii."""
    date_fmt = datetime.strptime(session["date"], "%Y-%m-%d").strftime("%-d. %-m. %Y") if session else ""
    html = f"""
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;color:#3a2e2a">
      <div style="background:#f5e6e0;padding:2rem;text-align:center;border-radius:12px 12px 0 0">
        <h1 style="font-weight:300;font-size:1.8rem;margin:0">✨ Magic<span style="color:#b89a7a">Space</span></h1>
      </div>
      <div style="background:#fdfaf8;padding:2rem;border-radius:0 0 12px 12px;border:1px solid #edddd6">
        <h2 style="font-weight:300;font-size:1.4rem">Rezervácia potvrdená</h2>
        <p>Ahoj <strong>{booking["name"]}</strong>,</p>
        <p>tvoja rezervácia bola prijatá. Tešíme sa na teba! 🌸</p>
        <div style="background:#f5e6e0;border-radius:10px;padding:1.2rem;margin:1.5rem 0">
          <strong style="font-size:1.1rem">{session["title"] if session else ""}</strong><br>
          📅 {date_fmt} &nbsp;·&nbsp; 🕐 {session["time"] if session else ""}<br>
          📍 {session["location"] if session else ""}<br>
          💰 {session["price"] if session else ""}
        </div>
        <p style="color:#7a6660;font-size:0.9rem">V prípade otázok ma kontaktuj na <a href="mailto:{ADMIN_EMAIL}" style="color:#b89a7a">{ADMIN_EMAIL}</a></p>
        <p style="color:#7a6660;font-size:0.9rem">Anastasia · MagicSpace</p>
        <hr style="border:none;border-top:1px solid #edddd6;margin:1.5rem 0">
        <p style="color:#b0a099;font-size:0.8rem">Nemôžeš prísť?
          <a href="{SITE_URL}/api/bookings/cancel?email={booking['email']}&sid={booking['session_id']}"
             style="color:#b89a7a">Zrušiť rezerváciu jedným kliknutím →</a>
        </p>
      </div>
    </div>"""
    send_email([booking["email"]], f"Rezervácia: {session['title'] if session else 'MagicSpace'}", html)

def email_booking_admin(booking, session):
    """Notifikácia adminu o novej rezervácii."""
    date_fmt = datetime.strptime(session["date"], "%Y-%m-%d").strftime("%-d. %-m. %Y") if session else ""
    html = f"""
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;color:#3a2e2a">
      <div style="background:#3a2e2a;padding:1.5rem;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:#fdfaf8;font-weight:300;font-size:1.4rem;margin:0">📅 Nová rezervácia</h1>
      </div>
      <div style="background:#fdfaf8;padding:2rem;border-radius:0 0 12px 12px;border:1px solid #edddd6">
        <table style="width:100%;border-collapse:collapse">
          <tr><td style="padding:0.4rem 0;color:#7a6660;width:120px">Meno</td><td><strong>{booking["name"]}</strong></td></tr>
          <tr><td style="padding:0.4rem 0;color:#7a6660">Email</td><td><a href="mailto:{booking["email"]}" style="color:#b89a7a">{booking["email"]}</a></td></tr>
          <tr><td style="padding:0.4rem 0;color:#7a6660">Telefón</td><td>{booking.get("phone","–")}</td></tr>
          <tr><td style="padding:0.4rem 0;color:#7a6660">Sésia</td><td><strong>{session["title"] if session else "–"}</strong></td></tr>
          <tr><td style="padding:0.4rem 0;color:#7a6660">Dátum</td><td>{date_fmt} {session["time"] if session else ""}</td></tr>
          <tr><td style="padding:0.4rem 0;color:#7a6660">Poznámka</td><td>{booking.get("note","–")}</td></tr>
        </table>
        <div style="margin-top:1.5rem">
          <a href="{SITE_URL}/admin.html" style="background:#b89a7a;color:#fff;padding:0.7rem 1.5rem;border-radius:50px;text-decoration:none;font-size:0.85rem">Otvoriť admin →</a>
        </div>
      </div>
    </div>"""
    send_email([ADMIN_EMAIL], f"Nová rezervácia – {booking['name']}", html)

def email_contact_admin(contact):
    """Notifikácia adminu o novej správe."""
    html = f"""
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;color:#3a2e2a">
      <div style="background:#3a2e2a;padding:1.5rem;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:#fdfaf8;font-weight:300;font-size:1.4rem;margin:0">✉️ Nová správa</h1>
      </div>
      <div style="background:#fdfaf8;padding:2rem;border-radius:0 0 12px 12px;border:1px solid #edddd6">
        <table style="width:100%;border-collapse:collapse">
          <tr><td style="padding:0.4rem 0;color:#7a6660;width:100px">Meno</td><td><strong>{contact["name"]}</strong></td></tr>
          <tr><td style="padding:0.4rem 0;color:#7a6660">Email</td><td><a href="mailto:{contact["email"]}" style="color:#b89a7a">{contact["email"]}</a></td></tr>
          <tr><td style="padding:0.4rem 0;color:#7a6660">Telefón</td><td>{contact.get("phone","–")}</td></tr>
          <tr><td style="padding:0.4rem 0;color:#7a6660">Téma</td><td>{contact.get("topic","–")}</td></tr>
        </table>
        <div style="background:#f5e6e0;border-radius:10px;padding:1rem;margin:1rem 0">
          <p style="margin:0">{contact.get("message","")}</p>
        </div>
        <a href="mailto:{contact["email"]}?subject=Re: {contact.get('topic','MagicSpace')}" style="background:#b89a7a;color:#fff;padding:0.7rem 1.5rem;border-radius:50px;text-decoration:none;font-size:0.85rem">Odpovedať →</a>
      </div>
    </div>"""
    send_email([ADMIN_EMAIL], f"Nová správa – {contact['name']}: {contact.get('topic','')}", html)

def email_reminder(booking, session):
    """Pripomienka 24h pred sesiou."""
    date_fmt = datetime.strptime(session["date"], "%Y-%m-%d").strftime("%-d. %-m. %Y")
    html = f"""
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;color:#3a2e2a">
      <div style="background:#c8d5c0;padding:2rem;text-align:center;border-radius:12px 12px 0 0">
        <h1 style="font-weight:300;font-size:1.6rem;margin:0">🌸 Zajtra ťa čakáme!</h1>
      </div>
      <div style="background:#fdfaf8;padding:2rem;border-radius:0 0 12px 12px;border:1px solid #edddd6">
        <p>Ahoj <strong>{booking["name"]}</strong>,</p>
        <p>pripomíname ti, že zajtra máš rezervované miesto:</p>
        <div style="background:#f5e6e0;border-radius:10px;padding:1.2rem;margin:1.5rem 0">
          <strong style="font-size:1.1rem">{session["title"]}</strong><br>
          📅 {date_fmt} &nbsp;·&nbsp; 🕐 {session["time"]}<br>
          📍 {session["location"]}
        </div>
        <p style="color:#7a6660;font-size:0.9rem">Ak sa nemôžeš zúčastniť, prosím daj vedieť čo najskôr.</p>
        <p style="color:#7a6660;font-size:0.9rem">Anastasia · MagicSpace · <a href="mailto:{ADMIN_EMAIL}" style="color:#b89a7a">{ADMIN_EMAIL}</a></p>
      </div>
    </div>"""
    send_email([booking["email"]], f"Pripomienka: {session['title']} – zajtra!", html)

def email_client_cancelled(booking, session):
    """Email klientovi – potvrdenie jeho vlastného zrušenia rezervácie."""
    date_fmt = datetime.strptime(session["date"], "%Y-%m-%d").strftime("%-d. %-m. %Y") if session else ""
    html = f"""
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;color:#3a2e2a">
      <div style="background:#d6e5d0;padding:2rem;text-align:center;border-radius:12px 12px 0 0">
        <h1 style="font-weight:300;font-size:1.6rem;margin:0">Rezervácia zrušená</h1>
      </div>
      <div style="background:#fdfaf8;padding:2rem;border-radius:0 0 12px 12px;border:1px solid #d6e5d0">
        <p>Ahoj <strong>{booking["name"]}</strong>,</p>
        <p>tvoja rezervácia bola úspešne zrušená. Ďakujeme, že si nám dala vedieť – miesto sme uvoľnili pre iného záujemcu.</p>
        <div style="background:#d6e5d0;border-radius:10px;padding:1.2rem;margin:1.5rem 0">
          <strong>{session["title"] if session else ""}</strong><br>
          📅 {date_fmt} &nbsp;·&nbsp; 🕐 {session["time"] if session else ""}
        </div>
        <p>Ak si to rozmyslíš, rezervuj si miesto znova:</p>
        <a href="{SITE_URL}/joga-park.html#lekcie" style="display:inline-block;background:#7a9e6e;color:#fff;padding:0.7rem 1.5rem;border-radius:50px;text-decoration:none;font-size:0.85rem">Rezervovať znova →</a>
        <p style="color:#7a6660;font-size:0.9rem;margin-top:1.5rem">Anastasia · MagicSpace · <a href="mailto:{ADMIN_EMAIL}" style="color:#b89a7a">{ADMIN_EMAIL}</a></p>
      </div>
    </div>"""
    send_email([booking["email"]], f"Zrušenie rezervácie: {session['title'] if session else 'MagicSpace'}", html)

def email_cancellation(booking, session):
    """Email klientovi o zrušení sésie."""
    html = f"""
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;color:#3a2e2a">
      <div style="background:#f0c8c0;padding:2rem;text-align:center;border-radius:12px 12px 0 0">
        <h1 style="font-weight:300;font-size:1.6rem;margin:0">Sésia bola zrušená</h1>
      </div>
      <div style="background:#fdfaf8;padding:2rem;border-radius:0 0 12px 12px;border:1px solid #edddd6">
        <p>Ahoj <strong>{booking["name"]}</strong>,</p>
        <p>s ľútosťou ti oznamujeme, že nasledujúca sésia musela byť zrušená:</p>
        <div style="background:#f5e6e0;border-radius:10px;padding:1.2rem;margin:1.5rem 0">
          <strong>{session["title"]}</strong><br>
          📅 {datetime.strptime(session["date"],"%Y-%m-%d").strftime("%-d. %-m. %Y")} · 🕐 {session["time"]}
        </div>
        <p>Ospravedlňujeme sa za nepríjemnosti. Čoskoro budem mať nové termíny.</p>
        <p style="color:#7a6660;font-size:0.9rem">Anastasia · MagicSpace · <a href="mailto:{ADMIN_EMAIL}" style="color:#b89a7a">{ADMIN_EMAIL}</a></p>
      </div>
    </div>"""
    send_email([booking["email"]], f"Zrušenie: {session['title']}", html)

# ─── SCHEDULER – pripomienky 24h pred ────────────────────────
def cleanup_old_sessions():
    """Zmaže sésie staršie ako 1 deň."""
    with get_db() as db:
        cur = db.execute("DELETE FROM sessions WHERE date < date('now', '-1 day')")
        db.commit()
        if cur.rowcount:
            print(f"🗑  Zmazaných {cur.rowcount} starých sésií")

def check_reminders():
    """Spúšťa sa každú hodinu. Pošle pripomienku 24h pred sesiou."""
    now       = datetime.now()
    tomorrow  = (now + timedelta(hours=24)).strftime("%Y-%m-%d")
    hour_now  = now.strftime("%H")

    with get_db() as db:
        # Najdi všetky rezervácie na zajtra, ktorým ešte nebola poslaná pripomienka
        rows = db.execute("""
            SELECT b.*, s.title, s.date, s.time, s.location, s.price
            FROM bookings b
            JOIN sessions s ON b.session_id = s.id
            WHERE s.date = ? AND b.reminded = 0 AND b.status != 'cancelled'
              AND s.badge != 'cancelled'
        """, (tomorrow,)).fetchall()

        for row in rows:
            booking = dict(row)
            session = {"title": row["title"], "date": row["date"],
                       "time": row["time"], "location": row["location"],
                       "price": row["price"]}
            email_reminder(booking, session)
            db.execute("UPDATE bookings SET reminded=1 WHERE id=?", (row["id"],))
        if rows:
            db.commit()
            print(f"⏰  Poslaných {len(rows)} pripomienok na {tomorrow}")

scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders,       "interval", hours=1)
scheduler.add_job(cleanup_old_sessions,  "interval", hours=24, next_run_time=datetime.now())
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ─── STATICKÉ STRÁNKY ─────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/<page>.html")
def static_page(page):
    path = os.path.join(BASE, f"{page}.html")
    if os.path.exists(path):
        return send_from_directory(BASE, f"{page}.html")
    abort(404)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOADS, filename)

@app.route("/jogamartin")
def jogamartin():
    return send_from_directory(BASE, "joga-park.html")

@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory(BASE, "sitemap.xml", mimetype="application/xml")

@app.route("/robots.txt")
def robots():
    return send_from_directory(BASE, "robots.txt", mimetype="text/plain")

# ─── AUTH CHECK ───────────────────────────────────────────────
@app.route("/api/auth", methods=["POST"])
def auth():
    data = request.json or {}
    if data.get("password") == ADMIN_PASSWORD:
        return jsonify({"ok": True})
    return jsonify({"error": "Nesprávne heslo"}), 401

# ─── API: UPLOAD OBRÁZKA ──────────────────────────────────────
@app.route("/api/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "Žiadny súbor"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Prázdny súbor"}), 400

    # Bezpečné meno súboru
    import re, time
    ext  = os.path.splitext(f.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        return jsonify({"error": "Povolené len obrázky (jpg, png, webp)"}), 400
    name = f"img_{int(time.time())}{ext}"
    f.save(os.path.join(UPLOADS, name))
    return jsonify({"url": f"/uploads/{name}"}), 201

# ─── API: SÉSIE ───────────────────────────────────────────────
@app.route("/api/sessions")
def list_sessions():
    project  = request.args.get("project", "main")
    upcoming = request.args.get("upcoming")   # e.g. "8" → next N future active sessions
    with get_db() as db:
        if upcoming:
            rows = db.execute(
                "SELECT * FROM sessions WHERE project=? AND date >= date('now') AND badge='active'"
                " ORDER BY date, time LIMIT ?",
                (project, int(upcoming))
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM sessions WHERE project=? ORDER BY date, time", (project,)
            ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/sessions", methods=["POST"])
def create_session():
    data = request.json
    if not all(data.get(k) for k in ["title", "date", "time"]):
        return jsonify({"error": "Chýbajú povinné polia"}), 400

    recur_type  = data.get("recur_type", "")
    recur_until = data.get("recur_until", "")

    with get_db() as db:
        cur = db.execute("""
            INSERT INTO sessions (title,date,time,duration,spots,price,desc,location,badge,project,image_url,recur_type,recur_until)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["title"], data["date"], data["time"],
            data.get("duration", "60 min"),
            int(data.get("spots", 10)),
            data.get("price", "0 €"),
            data.get("desc", ""),
            data.get("location", "Andreja Kmeťa 577/22, Martin"),
            data.get("badge", "active"),
            data.get("project", "main"),
            data.get("image_url", ""),
            recur_type,
            recur_until,
        ))
        db.commit()
        first_id = cur.lastrowid

        # Generovať opakujúce sa sésie
        if recur_type in ("weekly", "biweekly"):
            delta      = timedelta(weeks=1 if recur_type == "weekly" else 2)
            base_date  = datetime.strptime(data["date"], "%Y-%m-%d")
            end_date   = datetime.strptime(recur_until, "%Y-%m-%d") if recur_until else base_date + timedelta(weeks=13)
            cur_date   = base_date + delta
            while cur_date <= end_date:
                db.execute("""
                    INSERT INTO sessions
                      (title,date,time,duration,spots,price,desc,location,badge,project,image_url,
                       recur_type,recur_until,recur_parent_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    data["title"],
                    cur_date.strftime("%Y-%m-%d"),
                    data["time"],
                    data.get("duration", "60 min"),
                    int(data.get("spots", 10)),
                    data.get("price", "0 €"),
                    data.get("desc", ""),
                    data.get("location", "Andreja Kmeťa 577/22, Martin"),
                    "active",
                    data.get("project", "main"),
                    data.get("image_url", ""),
                    recur_type,
                    recur_until,
                    first_id,
                ))
                cur_date += delta
            db.commit()

        row = db.execute("SELECT * FROM sessions WHERE id=?", (first_id,)).fetchone()
    return jsonify(dict(row)), 201

@app.route("/api/sessions/<int:sid>", methods=["PUT"])
def update_session(sid):
    data  = request.json
    fields = ["title","date","time","duration","spots","price","desc","location","badge","image_url"]
    sets   = ", ".join(f"{f}=?" for f in fields if f in data)
    vals   = [data[f] for f in fields if f in data] + [sid]
    if not sets:
        return jsonify({"error": "Nič na aktualizáciu"}), 400
    with get_db() as db:
        db.execute(f"UPDATE sessions SET {sets} WHERE id=?", vals)
        db.commit()
        row = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    return jsonify(dict(row))

@app.route("/api/sessions/<int:sid>", methods=["DELETE"])
def delete_session(sid):
    with get_db() as db:
        db.execute("DELETE FROM sessions WHERE id=?", (sid,))
        db.commit()
    return jsonify({"ok": True})

@app.route("/api/sessions/<int:sid>/recur-group", methods=["DELETE"])
def delete_recur_group(sid):
    """Zmaže celú sériu opakujúcich sa sésií."""
    with get_db() as db:
        row = db.execute("SELECT recur_parent_id FROM sessions WHERE id=?", (sid,)).fetchone()
        if not row:
            return jsonify({"error": "Nenájdená"}), 404
        parent_id = row["recur_parent_id"] or sid
        db.execute("DELETE FROM sessions WHERE recur_parent_id=? OR id=?", (parent_id, parent_id))
        db.commit()
    return jsonify({"ok": True})

@app.route("/api/sessions/<int:sid>/cancel", methods=["POST"])
def cancel_session(sid):
    with get_db() as db:
        row = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
        if not row:
            return jsonify({"error": "Nenájdená"}), 404
        new_badge = "active" if row["badge"] == "cancelled" else "cancelled"
        db.execute("UPDATE sessions SET badge=? WHERE id=?", (new_badge, sid))
        db.commit()

        # Ak sa sésia RUŠÍ → email všetkým prihlaseným
        if new_badge == "cancelled":
            bookings = db.execute(
                "SELECT * FROM bookings WHERE session_id=? AND status!='cancelled'", (sid,)
            ).fetchall()
            session_data = dict(row)
            for b in bookings:
                email_cancellation(dict(b), session_data)

        row = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    return jsonify(dict(row))

# ─── API: REZERVÁCIE ──────────────────────────────────────────
@app.route("/api/bookings")
def list_bookings():
    with get_db() as db:
        rows = db.execute("""
            SELECT b.*, s.title as session_title, s.date as session_date,
                   s.time as session_time, s.location as session_location,
                   s.price as session_price, s.project
            FROM bookings b
            LEFT JOIN sessions s ON b.session_id = s.id
            ORDER BY b.created_at DESC
        """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data = request.json
    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "Chýba meno alebo email"}), 400
    sid = data.get("session_id")
    session = None

    with get_db() as db:
        if sid:
            session = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
            if not session:
                return jsonify({"error": "Sésia neexistuje"}), 404
            if session["booked"] >= session["spots"] or session["badge"] in ("full","cancelled"):
                return jsonify({"error": "Sésia je plná alebo zrušená"}), 409

        cur = db.execute("""
            INSERT INTO bookings (session_id,name,email,phone,note,status,terms_accepted)
            VALUES (?,?,?,?,?,?,?)
        """, (sid, data["name"], data["email"],
              data.get("phone",""), data.get("note",""), "confirmed",
              1 if data.get("terms_accepted") else 0))

        if sid:
            db.execute("UPDATE sessions SET booked=booked+1 WHERE id=?", (sid,))
        db.commit()

        booking = dict(db.execute("SELECT * FROM bookings WHERE id=?", (cur.lastrowid,)).fetchone())
        if session:
            session = dict(session)

    # Emaily v pozadí
    if session:
        email_booking_client(booking, session)
        email_booking_admin(booking, session)

    return jsonify(booking), 201

@app.route("/api/bookings/<int:bid>/confirm", methods=["POST"])
def confirm_booking(bid):
    with get_db() as db:
        db.execute("UPDATE bookings SET status='confirmed' WHERE id=?", (bid,))
        db.commit()
        row = db.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
    return jsonify(dict(row))

@app.route("/api/bookings/<int:bid>", methods=["DELETE"])
def delete_booking(bid):
    with get_db() as db:
        b = db.execute("SELECT session_id FROM bookings WHERE id=?", (bid,)).fetchone()
        if b and b["session_id"]:
            db.execute("UPDATE sessions SET booked=MAX(booked-1,0) WHERE id=?", (b["session_id"],))
        db.execute("DELETE FROM bookings WHERE id=?", (bid,))
        db.commit()
    return jsonify({"ok": True})

@app.route("/api/bookings/cancel-by-email", methods=["POST"])
def cancel_by_email():
    """Klient zruší svoju rezerváciu podľa emailu (z formulára na stránke)."""
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "Zadajte platný e-mail"}), 400
    sid = data.get("session_id")
    with get_db() as db:
        if sid:
            rows = db.execute(
                """SELECT b.*, s.title, s.date, s.time FROM bookings b
                   LEFT JOIN sessions s ON b.session_id=s.id
                   WHERE lower(trim(b.email))=? AND b.session_id=? AND b.status!='cancelled'""",
                (email, sid)
            ).fetchall()
        else:
            rows = db.execute(
                """SELECT b.*, s.title, s.date, s.time FROM bookings b
                   LEFT JOIN sessions s ON b.session_id=s.id
                   WHERE lower(trim(b.email))=? AND b.status!='cancelled'
                     AND (s.date IS NULL OR s.date >= date('now'))""",
                (email,)
            ).fetchall()
        if not rows:
            return jsonify({"cancelled": 0, "message": "Rezervácia na tento e-mail nebola nájdená"})
        for row in rows:
            db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (row["id"],))
            if row["session_id"]:
                db.execute("UPDATE sessions SET booked=MAX(booked-1,0) WHERE id=?", (row["session_id"],))
            email_client_cancelled(dict(row), dict(row))
        db.commit()
    return jsonify({"cancelled": len(rows), "message": "Rezervácia bola zrušená"})

@app.route("/api/bookings/cancel")
def cancel_by_link():
    """One-click zrušenie z emailu: /api/bookings/cancel?email=X&sid=Y"""
    email = (request.args.get("email") or "").strip().lower()
    sid   = request.args.get("sid", type=int)
    ok, msg = False, "Rezervácia nenájdená"
    if email and sid:
        with get_db() as db:
            row = db.execute(
                """SELECT b.*, s.title, s.date, s.time FROM bookings b
                   LEFT JOIN sessions s ON b.session_id=s.id
                   WHERE lower(trim(b.email))=? AND b.session_id=? AND b.status!='cancelled'""",
                (email, sid)
            ).fetchone()
            if row:
                db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (row["id"],))
                db.execute("UPDATE sessions SET booked=MAX(booked-1,0) WHERE id=?", (sid,))
                db.commit()
                email_client_cancelled(dict(row), dict(row))
                ok, msg = True, "Rezervácia bola zrušená"
    color  = "#7a9e6e" if ok else "#c0a090"
    icon   = "✓" if ok else "✗"
    return f"""<!DOCTYPE html><html lang="sk"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{msg} · Magic Space</title>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400&family=Jost:wght@300;400&display=swap" rel="stylesheet">
    </head><body style="margin:0;background:#f0f4ee;font-family:'Jost',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;">
    <div style="background:#fdfaf8;border-radius:24px;padding:3rem 2.5rem;max-width:420px;width:90%;text-align:center;box-shadow:0 4px 32px rgba(42,51,40,0.08)">
      <div style="width:64px;height:64px;border-radius:50%;background:{color};color:#fff;font-size:2rem;display:flex;align-items:center;justify-content:center;margin:0 auto 1.5rem">{icon}</div>
      <h1 style="font-family:'Cormorant Garamond',serif;font-weight:300;font-size:2rem;color:#2a3328;margin:0 0 0.8rem">{msg}</h1>
      <p style="color:#5a6e5a;font-size:0.9rem;line-height:1.7;margin:0 0 2rem">{"Ďakujeme, že si nám dal(a) vedieť. Miesto sme uvoľnili pre iného záujemcu." if ok else "Rezervácia nebola nájdená alebo už bola zrušená."}</p>
      <a href="{SITE_URL}/joga-park.html" style="display:inline-block;background:#7a9e6e;color:#fff;text-decoration:none;padding:0.85rem 2rem;border-radius:50px;font-size:0.8rem;letter-spacing:0.1em;text-transform:uppercase">Späť na stránku →</a>
    </div></body></html>"""

# ─── API: KLIENTI ────────────────────────────────────────────
@app.route("/api/clients")
def list_clients():
    """Unikátni klienti zo všetkých rezervácií."""
    with get_db() as db:
        rows = db.execute("""
            SELECT
                name, email, phone,
                COUNT(*)                    AS total_bookings,
                MAX(created_at)             AS last_booking,
                MAX(terms_accepted)         AS terms_accepted
            FROM bookings
            GROUP BY lower(trim(email))
            ORDER BY last_booking DESC
        """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/clients/send-email", methods=["POST"])
def send_client_email():
    """Pošle email jednému klientovi alebo všetkým."""
    data    = request.json or {}
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()
    to      = data.get("to", "")   # email alebo "all"

    if not subject or not message:
        return jsonify({"error": "Chýba predmet alebo správa"}), 400

    html_body = f"""
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;color:#3a2e2a">
      <div style="background:#f5e6e0;padding:2rem;text-align:center;border-radius:12px 12px 0 0">
        <h1 style="font-weight:300;font-size:1.8rem;margin:0">&#10027; Magic<span style="color:#b89a7a">Space</span></h1>
      </div>
      <div style="background:#fdfaf8;padding:2rem;border-radius:0 0 12px 12px;border:1px solid #edddd6">
        {message.replace(chr(10), '<br>')}
        <p style="color:#7a6660;font-size:0.85rem;margin-top:2rem">
          Anastasia &middot; MagicSpace &middot;
          <a href="mailto:{ADMIN_EMAIL}" style="color:#b89a7a">{ADMIN_EMAIL}</a>
        </p>
      </div>
    </div>"""

    with get_db() as db:
        if to == "all":
            rows = db.execute(
                "SELECT DISTINCT lower(trim(email)) AS email FROM bookings"
            ).fetchall()
            recipients = [r["email"] for r in rows if r["email"]]
        else:
            recipients = [to]

    if not recipients:
        return jsonify({"error": "Žiadni príjemcovia"}), 400

    for addr in recipients:
        send_email([addr], subject, html_body)

    return jsonify({"ok": True, "sent": len(recipients)})

# ─── API: KONTAKTY ────────────────────────────────────────────
@app.route("/api/contacts")
def list_contacts():
    with get_db() as db:
        rows = db.execute("SELECT * FROM contacts ORDER BY created_at DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/contacts", methods=["POST"])
def create_contact():
    data = request.json
    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "Chýba meno alebo email"}), 400
    with get_db() as db:
        cur = db.execute("""
            INSERT INTO contacts (name,email,phone,topic,message)
            VALUES (?,?,?,?,?)
        """, (data["name"], data["email"], data.get("phone",""),
              data.get("topic",""), data.get("message","")))
        db.commit()
        contact = dict(db.execute("SELECT * FROM contacts WHERE id=?", (cur.lastrowid,)).fetchone())

    email_contact_admin(contact)
    return jsonify(contact), 201

@app.route("/api/contacts/<int:cid>", methods=["DELETE"])
def delete_contact(cid):
    with get_db() as db:
        db.execute("DELETE FROM contacts WHERE id=?", (cid,))
        db.commit()
    return jsonify({"ok": True})

@app.route("/api/contacts/<int:cid>/read", methods=["POST"])
def mark_contact_read(cid):
    with get_db() as db:
        db.execute("UPDATE contacts SET status='read' WHERE id=?", (cid,))
        db.commit()
    return jsonify({"ok": True})

# ─── KURZ CLICK TRACKING ─────────────────────────────────────
BUNDLE_SUMUP_URL = os.getenv("BUNDLE_SUMUP_URL", "https://pay.sumup.com/b2c/QLZBCS4G")


@app.route("/go/bundle")
def go_bundle():
    e = request.args.get("e", "")
    if e:
        try:
            email = base64.urlsafe_b64decode(e + "==").decode()
            with get_db() as db:
                db.execute(
                    "UPDATE subscribers SET kurz_interest_at=COALESCE(NULLIF(kurz_interest_at,''),?), guide_interest_at=COALESCE(NULLIF(guide_interest_at,''),?) WHERE email=?",
                    [datetime.now().isoformat(), datetime.now().isoformat(), email]
                )
                db.commit()
        except Exception:
            pass
    return redirect(BUNDLE_SUMUP_URL)


@app.route("/go/partner-guide")
def go_partner_guide():
    e = request.args.get("e", "")
    if e:
        try:
            email = base64.urlsafe_b64decode(e + "==").decode()
            with get_db() as db:
                db.execute(
                    "UPDATE subscribers SET guide_interest_at=? WHERE email=? AND (guide_interest_at IS NULL OR guide_interest_at='')",
                    [datetime.now().isoformat(), email]
                )
                db.commit()
        except Exception:
            pass
    return redirect("https://pay.sumup.com/b2c/QC3SD8JE")


@app.route("/go/kurz")
def go_kurz():
    e = request.args.get("e", "")
    if e:
        try:
            email = base64.urlsafe_b64decode(e + "==").decode()
            with get_db() as db:
                db.execute(
                    "UPDATE subscribers SET kurz_interest_at=? WHERE email=? AND (kurz_interest_at IS NULL OR kurz_interest_at='')",
                    [datetime.now().isoformat(), email]
                )
                db.commit()
        except Exception:
            pass
    return redirect(f"{SITE_URL}/kurz.html")

# ─── API: PRE-CHECKOUT & CONFIRM ─────────────────────────────
SUMUP_URLS = {
    "kurz":   "https://pay.sumup.com/b2c/Q51A04KE",
    "bundle": "https://pay.sumup.com/b2c/QLZBCS4G",
    "guide":  "https://pay.sumup.com/b2c/QC3SD8JE",
}
PRODUCT_NAMES = {
    "kurz":   "Kurz prípravy na pôrod (59 €)",
    "bundle": "Kurz + Manuál pre partnera (67 €)",
    "guide":  "Manuál pre partnera – PDF (15 €)",
}


@app.route("/api/pre-checkout", methods=["POST"])
def pre_checkout():
    data    = request.get_json(silent=True) or {}
    email   = (data.get("email") or "").strip().lower()
    product = (data.get("product") or "kurz").strip()
    if not email or "@" not in email or product not in SUMUP_URLS:
        return jsonify({"redirect": SUMUP_URLS.get(product, SUMUP_URLS["kurz"])}), 200

    token = secrets.token_urlsafe(24)
    with get_db() as db:
        db.execute(
            "INSERT INTO purchases (email, product, token) VALUES (?,?,?)",
            (email, product, token)
        )
        db.commit()

    confirm_url = f"{SITE_URL}/api/confirm-payment?token={token}"
    product_name = PRODUCT_NAMES.get(product, product)
    admin_html = f"""
    <div style="font-family:Georgia,serif;max-width:520px;margin:0 auto;color:#3a2e2a">
      <div style="background:#3a2e2a;padding:1.5rem 2rem;border-radius:12px 12px 0 0">
        <h2 style="color:#fdfaf8;font-weight:300;font-size:1.3rem;margin:0">
          Nová platba – skontroluj SumUp
        </h2>
      </div>
      <div style="background:#fdfaf8;padding:1.8rem 2rem;border-radius:0 0 12px 12px;border:1px solid #edddd6">
        <table style="width:100%;border-collapse:collapse">
          <tr><td style="padding:0.4rem 0;color:#8a7f78;width:100px">Email</td>
              <td><strong>{email}</strong></td></tr>
          <tr><td style="padding:0.4rem 0;color:#8a7f78">Produkt</td>
              <td><strong>{product_name}</strong></td></tr>
        </table>
        <p style="margin:1.2rem 0 0.6rem;font-size:0.85rem;color:#584840">
          Skontroluj SumUp či platba prešla, potom klikni:
        </p>
        <a href="{confirm_url}"
           style="display:inline-block;background:#b89a7a;color:#fff;text-decoration:none;
                  padding:0.85rem 2rem;border-radius:50px;font-size:0.82rem;
                  letter-spacing:0.1em;text-transform:uppercase">
          ✓ &nbsp;Potvrdiť platbu a poslať klientovi
        </a>
        <p style="margin:1rem 0 0;font-size:0.75rem;color:#8a7f78">
          Alebo ignoruj ak platba neprešla.
        </p>
      </div>
    </div>"""
    send_email([ADMIN_EMAIL], f"Nová platba – {product_name} · {email}", admin_html)
    return jsonify({"redirect": SUMUP_URLS[product]})


@app.route("/api/confirm-payment")
def confirm_payment():
    token = request.args.get("token", "")
    if not token:
        return "Neplatný odkaz.", 400

    with get_db() as db:
        row = db.execute(
            "SELECT * FROM purchases WHERE token=?", (token,)
        ).fetchone()
        if not row:
            return "Odkaz neexistuje alebo bol už použitý.", 400
        if row["status"] == "confirmed":
            return _confirm_success_page(row["email"], row["product"], already=True)
        db.execute("UPDATE purchases SET status='confirmed' WHERE token=?", (token,))
        db.commit()

    _send_purchase_confirmation(row["email"], row["product"])
    return _confirm_success_page(row["email"], row["product"])


def _send_purchase_confirmation(email, product):
    if product == "guide":
        tpl_path = os.path.join(BASE, "content", "sk", "emails", "kurz_confirm.html")
        try:
            with open(tpl_path, encoding="utf-8") as f:
                html = f.read()
            download_url = f"{SITE_URL}/partner-guide-download.html"
            block = (
                f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px">'
                f'<tr><td style="text-align:center">'
                f'<a href="{download_url}" style="display:inline-block;background:#b89a7a;color:#fff;'
                f'text-decoration:none;padding:14px 32px;border-radius:50px;font-family:Arial,sans-serif;'
                f'font-size:12px;letter-spacing:0.12em;text-transform:uppercase">'
                f'Stiahnuť manuál pre partnera →</a></td></tr></table>'
            )
            html = html.replace("{{kurz_date}}", "")
            html = html.replace('<p style="margin:0 0 18px;font-size:15px;color:#3a2e2a;line-height:1.85">platba prebehla',
                                block + '<p style="margin:0 0 18px;font-size:15px;color:#3a2e2a;line-height:1.85">Manuál je tvoj –')
            send_email([email], "Tvoj manuál pre partnera – Magic Space", html)
        except Exception as e:
            print(f"guide confirm email error: {e}")
    elif product == "bundle":
        tpl_path = os.path.join(BASE, "content", "sk", "emails", "kurz_confirm.html")
        try:
            with open(tpl_path, encoding="utf-8") as f:
                html = f.read()
            download_url = f"{SITE_URL}/bundle-download.html"
            html = html.replace("{{kurz_date}}", "4. júla alebo 12. septembra 2026")
            html = html.replace("Tešíme sa na vás oboch", f'Máš oboje – <a href="{download_url}" style="color:#b89a7a">stiahnuť manuál →</a>')
            send_email([email], "Kurz + Manuál zakúpený – Magic Space", html)
        except Exception as e:
            print(f"bundle confirm email error: {e}")
    else:
        _send_kurz_confirm_email(email)


def _confirm_success_page(email, product, already=False):
    msg = "Potvrdenie bolo už odoslané." if already else "Potvrdenie odoslané klientovi."
    return f"""<!DOCTYPE html><html lang="sk"><head><meta charset="UTF-8">
    <title>Platba potvrdená</title>
    <link href="https://fonts.googleapis.com/css2?family=Jost:wght@300;400&display=swap" rel="stylesheet">
    </head><body style="margin:0;background:#f0ebe6;font-family:'Jost',sans-serif;
    display:flex;align-items:center;justify-content:center;min-height:100vh">
    <div style="background:#fdfaf8;border-radius:20px;padding:2.5rem 2rem;max-width:380px;
    text-align:center;box-shadow:0 4px 24px rgba(58,46,42,0.08)">
      <div style="width:52px;height:52px;border-radius:50%;background:#b89a7a;color:#fff;
      font-size:1.4rem;display:flex;align-items:center;justify-content:center;margin:0 auto 1.2rem">✓</div>
      <h2 style="font-weight:400;font-size:1.3rem;color:#3a2e2a;margin:0 0 0.6rem">{msg}</h2>
      <p style="font-size:0.85rem;color:#8a7f78;margin:0 0 1.4rem">{email} · {PRODUCT_NAMES.get(product,'')}</p>
      <a href="{SITE_URL}/admin.html" style="font-size:0.78rem;color:#b89a7a;text-decoration:none">← Admin</a>
    </div></body></html>"""


# ─── API: KURZ INTEREST ──────────────────────────────────────
@app.route("/api/kurz-interest", methods=["POST"])
def kurz_interest():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    date  = (data.get("date") or "").strip()
    if not email or not date:
        return jsonify({"ok": True})
    with get_db() as db:
        db.execute("""
            INSERT INTO contacts (name, email, topic, message)
            VALUES (?, ?, 'Kurz – záujem', ?)
        """, ("—", email, f"Termín: {date}"))
        db.commit()
    # Notifikácia adminu
    send_email([ADMIN_EMAIL],
        f"Nový záujem o kurz – {date}",
        f"<p>Email: <strong>{email}</strong><br>Termín: <strong>{date}</strong></p>")
    return jsonify({"ok": True})

# ─── API: KURZ REGISTER (from thank-you page) ────────────
@app.route("/api/kurz-register", methods=["POST"])
def kurz_register():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"ok": True})
    with get_db() as db:
        existing = db.execute("SELECT id FROM subscribers WHERE email=?", (email,)).fetchone()
        if existing:
            db.execute("UPDATE subscribers SET kurz_confirmed=1 WHERE email=?", (email,))
        else:
            db.execute(
                "INSERT INTO subscribers (email, source, kurz_confirmed) VALUES (?,?,1)",
                (email, "kurz-dekujeme")
            )
        db.commit()
    _send_kurz_confirm_email(email)
    return jsonify({"ok": True})


def _send_kurz_confirm_email(email):
    tpl_path = os.path.join(BASE, "content", "sk", "emails", "kurz_confirm.html")
    try:
        with open(tpl_path, encoding="utf-8") as f:
            html = f.read()
        html = html.replace("{{kurz_date}}", "4. júla 2026 alebo 12. septembra 2026")
        send_email([email], "Prihlásenie na kurz potvrdené – Magic Space", html)
    except Exception as e:
        print(f"kurz_confirm email error: {e}")


# ─── API: SUBSCRIBE ──────────────────────────────────────────
@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    hp    = data.get("hp_name", "")  # honeypot
    if hp:
        return jsonify({"ok": True})  # bot — тихо игнорируем
    if not email or "@" not in email:
        return jsonify({"error": "Zadajte platný e-mail"}), 400
    if not data.get("consent"):
        return jsonify({"error": "Súhlas je povinný"}), 400
    due_date = (data.get("due_date") or "").strip()
    with get_db() as db:
        existing = db.execute("SELECT id FROM subscribers WHERE email=?", (email,)).fetchone()
        if not existing:
            db.execute("INSERT INTO subscribers (email, due_date, source) VALUES (?,?,?)", (email, due_date, "landing"))
        else:
            if due_date:
                db.execute("UPDATE subscribers SET due_date=? WHERE email=?", (due_date, email))
        db.commit()
    _send_welcome_email(email)
    return jsonify({"ok": True})

def _send_welcome_email(email):
    tpl_path = os.path.join(BASE, "content", "sk", "emails", "nurture_1.html")
    with open(tpl_path, encoding="utf-8") as f:
        html = f.read()
    unsubscribe_url = f"{SITE_URL}/unsubscribe?email={email}"
    html = html.replace("{{unsubscribe_url}}", unsubscribe_url)
    tg_link = create_invite_link()
    if tg_link:
        tg_block = (
            f'<table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px">'
            f'<tr><td style="background:#f5e6e0;border-radius:14px;padding:18px 22px;text-align:center">'
            f'<p style="margin:0 0 4px;font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:#b89a7a">Telegram kanál</p>'
            f'<p style="margin:0 0 12px;font-size:14px;color:#3a2e2a;line-height:1.6">Pridajte sa do nášho súkromného kanála –<br>tipy, pripomienky a komunita pred pôrodom.</p>'
            f'<a href="{tg_link}" style="display:inline-block;background:#3a2e2a;color:#fff;text-decoration:none;'
            f'padding:11px 28px;border-radius:50px;font-family:Arial,sans-serif;font-size:12px;letter-spacing:0.1em;text-transform:uppercase">'
            f'Vstúpiť do kanála →</a></td></tr></table>'
        )
        html = html.replace("</td></tr>\n\n    <!-- footer -->", tg_block + "</td></tr>\n\n    <!-- footer -->")
    send_email([email], "Váš sprievodca ku pôrodu – MagicSpace", html)


@app.route("/api/telegram-webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(silent=True) or {}
    threading.Thread(target=handle_update, args=(update,), daemon=True).start()
    return "", 200

# ─── API: RECENZIE ───────────────────────────────────────────
@app.route("/api/reviews")
def list_reviews():
    page = request.args.get("page", "dula")
    with get_db() as db:
        rows = db.execute(
            "SELECT id,name,stars,text,created_at FROM reviews WHERE page=? AND status='approved' ORDER BY created_at DESC",
            (page,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/unsubscribe")
def unsubscribe():
    email = request.args.get("email", "").strip().lower()
    if email and "@" in email:
        with get_db() as db:
            db.execute("DELETE FROM subscribers WHERE email=?", (email,))
            db.commit()
    return """<!DOCTYPE html><html lang="sk"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Odhlásenie | Magic Space</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,400&family=Jost:wght@300;400&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:'Jost',sans-serif;background:#f0ebe6;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.card{background:#fdfaf8;border-radius:20px;padding:2.8rem 2.4rem;max-width:400px;text-align:center;box-shadow:0 4px 24px rgba(58,46,42,0.08)}
.brand{font-family:'Cormorant Garamond',serif;font-size:1rem;letter-spacing:0.18em;text-transform:uppercase;color:#b89a7a;margin-bottom:1.8rem;display:block}
h1{font-family:'Cormorant Garamond',serif;font-size:1.8rem;font-weight:300;color:#3a2e2a;margin-bottom:0.8rem}
p{font-size:0.88rem;color:#4a3530;line-height:1.8;margin-bottom:1.6rem}
a{display:inline-block;color:#b89a7a;font-size:0.8rem;text-decoration:none;border-bottom:1px solid rgba(184,154,122,0.4);padding-bottom:1px}</style></head>
<body><div class="card">
<span class="brand">MagicSpace</span>
<h1>Odhlásenie prebehlo</h1>
<p>Vaša e-mailová adresa bola odstránená zo zoznamu. Nebudete dostávať ďalšie správy.</p>
<a href="https://magicspace.sk">← Späť na magicspace.sk</a>
</div></body></html>""", 200

@app.route("/api/reviews/admin")
def list_reviews_admin():
    with get_db() as db:
        rows = db.execute("SELECT * FROM reviews ORDER BY created_at DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/reviews", methods=["POST"])
def create_review():
    data = request.json or {}
    if not data.get("name") or not data.get("text") or not data.get("page"):
        return jsonify({"error": "Chýbajú povinné polia"}), 400
    stars = max(1, min(5, int(data.get("stars", 5))))
    with get_db() as db:
        db.execute(
            "INSERT INTO reviews (page,name,email,stars,text) VALUES (?,?,?,?,?)",
            (data["page"], data["name"], data.get("email",""), stars, data["text"])
        )
        db.commit()
    return jsonify({"ok": True}), 201

@app.route("/api/reviews/<int:rid>/approve", methods=["POST"])
def approve_review(rid):
    with get_db() as db:
        db.execute("UPDATE reviews SET status='approved' WHERE id=?", (rid,))
        db.commit()
    return jsonify({"ok": True})

@app.route("/api/reviews/<int:rid>", methods=["DELETE"])
def delete_review(rid):
    with get_db() as db:
        db.execute("DELETE FROM reviews WHERE id=?", (rid,))
        db.commit()
    return jsonify({"ok": True})

# ─── STATS ───────────────────────────────────────────────────
@app.route("/api/stats")
def stats():
    with get_db() as db:
        active    = db.execute("SELECT COUNT(*) FROM sessions WHERE badge='active'").fetchone()[0]
        bookings  = db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        pending   = db.execute("SELECT COUNT(*) FROM bookings WHERE status='pending'").fetchone()[0]
        contacts  = db.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        new_c     = db.execute("SELECT COUNT(*) FROM contacts WHERE status='new'").fetchone()[0]
        t_spots   = db.execute("SELECT SUM(spots) FROM sessions").fetchone()[0] or 0
        t_booked  = db.execute("SELECT SUM(booked) FROM sessions").fetchone()[0] or 0
        upcoming  = db.execute(
            "SELECT * FROM sessions WHERE date >= date('now') AND badge='active' ORDER BY date,time LIMIT 3"
        ).fetchall()
    return jsonify({
        "active_sessions":  active,
        "total_bookings":   bookings,
        "pending_bookings": pending,
        "total_contacts":   contacts,
        "new_contacts":     new_c,
        "occupancy_pct":    round(t_booked / t_spots * 100) if t_spots else 0,
        "upcoming":         [dict(r) for r in upcoming],
    })

# Inicializácia DB pri štarte (funguje aj s Gunicorn/WSGI)
init_db()

# ─── SPUSTENIE ───────────────────────────────────────────────
if __name__ == "__main__":
    print("\n✨ MagicSpace server beží!")
    print("   Web:   http://localhost:5000")
    print("   Admin: http://localhost:5000/admin.html")
    print("\n📧 Email nastavenia:")
    print(f"   Admin email: {ADMIN_EMAIL}")
    if not MAIL_PASS or "xxxx" in MAIL_PASS:
        print("   ⚠️  GMAIL_PASS nie je nastavené – emaily nebudú fungovať")
        print("   → Návod: https://support.google.com/accounts/answer/185833")
    print("\n   Zastavte: Ctrl+C\n")
    app.run(
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )

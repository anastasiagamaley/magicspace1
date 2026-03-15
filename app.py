"""
MagicSpace – Flask backend
Spustite:  python app.py
Otvorte:   http://localhost:5000
"""

from flask import Flask, jsonify, request, send_from_directory, abort
import sqlite3, os, json, smtplib, threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

BASE    = os.path.dirname(os.path.abspath(__file__))
DB      = os.path.join(BASE, "magicspace.db")
UPLOADS = os.path.join(BASE, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

app = Flask(__name__, static_folder=BASE, static_url_path="")

# ════════════════════════════════════════════════════════════════
# NASTAVENIA – ZMEŇTE TIETO HODNOTY
# ════════════════════════════════════════════════════════════════
ADMIN_EMAIL    = "anastasiagamaley@gmail.com"   # váš email
GMAIL_USER     = "anastasiagamaley@gmail.com"   # Gmail odosielateľ
GMAIL_PASS     = "bobz gimd mvcj asop"          # App Password (nie heslo do Gmailu!)
ADMIN_PASSWORD = "admin123"                      # heslo do adminpanelu
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
        """)

        # Pridať stĺpec image_url ak ešte neexistuje (pre existujúce DB)
        try:
            db.execute("ALTER TABLE sessions ADD COLUMN image_url TEXT DEFAULT ''")
            db.commit()
        except:
            pass

        try:
            db.execute("ALTER TABLE bookings ADD COLUMN reminded INTEGER DEFAULT 0")
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
                 "Park pri Kotline, Martin","active","park"),
                ("Večerná joga v parku","2025-06-04","18:00","60 min",20,12,"8 €",
                 "Uzavrite pracovný deň pohybom v prírode.",
                 "Park pri Kotline, Martin","active","park"),
            ])
            db.commit()

# ─── EMAIL ───────────────────────────────────────────────────
def send_email(to_list, subject, html_body):
    """Odošle email na zoznam adresátov. Spustí sa vo vlákne aby neblokoval server."""
    def _send():
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"MagicSpace <{GMAIL_USER}>"
            msg["To"]      = ", ".join(to_list)
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, to_list, msg.as_string())
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
          <a href="http://localhost:5000/admin.html" style="background:#b89a7a;color:#fff;padding:0.7rem 1.5rem;border-radius:50px;text-decoration:none;font-size:0.85rem">Otvoriť admin →</a>
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
scheduler.add_job(check_reminders, "interval", hours=1)
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
    project = request.args.get("project", "main")
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM sessions WHERE project=? ORDER BY date, time", (project,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/sessions", methods=["POST"])
def create_session():
    data = request.json
    if not all(data.get(k) for k in ["title", "date", "time"]):
        return jsonify({"error": "Chýbajú povinné polia"}), 400
    with get_db() as db:
        cur = db.execute("""
            INSERT INTO sessions (title,date,time,duration,spots,price,desc,location,badge,project,image_url)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
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
        ))
        db.commit()
        row = db.execute("SELECT * FROM sessions WHERE id=?", (cur.lastrowid,)).fetchone()
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
            INSERT INTO bookings (session_id,name,email,phone,note)
            VALUES (?,?,?,?,?)
        """, (sid, data["name"], data["email"],
              data.get("phone",""), data.get("note","")))

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

# ─── SPUSTENIE ───────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("\n✨ MagicSpace server beží!")
    print("   Web:   http://localhost:5000")
    print("   Admin: http://localhost:5000/admin.html")
    print("\n📧 Email nastavenia:")
    print(f"   Admin email: {ADMIN_EMAIL}")
    if "xxxx" in GMAIL_PASS:
        print("   ⚠️  GMAIL_PASS nie je nastavené – emaily nebudú fungovať")
        print("   → Návod: https://support.google.com/accounts/answer/185833")
    print("\n   Zastavte: Ctrl+C\n")
    app.run(debug=True, host="0.0.0.0", port=5000)

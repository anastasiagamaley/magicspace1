import os, requests, logging

log = logging.getLogger(__name__)

BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"


def create_invite_link() -> str:
    """One-time invite link to the private channel (member_limit=1)."""
    if not BOT_TOKEN or not CHANNEL_ID:
        return ""
    try:
        r = requests.post(f"{TG}/createChatInviteLink", json={
            "chat_id":      CHANNEL_ID,
            "member_limit": 1,
            "name":         "welcome",
        }, timeout=10)
        data = r.json()
        if data.get("ok"):
            return data["result"]["invite_link"]
        log.error("TG invite error: %s", data)
    except Exception as e:
        log.error("TG invite exception: %s", e)
    return ""


# ── FAQ answers (used by the webhook handler) ─────────────────
FAQ = {
    "fazy": (
        "🌸 *Fázy pôrodu*\n\n"
        "*1. Latentná fáza* – kontrakcie každých 5–20 min, trvá hodiny (aj celú noc). Zostaňte doma, odpočívajte.\n\n"
        "*2. Aktívna fáza* – kontrakcie každé 3–5 min, 45–60 sekúnd. Čas ísť do pôrodnice.\n\n"
        "*3. Prechodná fáza* – najintenzívnejšia, ale najkratšia (30–60 min). Krčok sa otvára na 10 cm.\n\n"
        "*4. Tlačenie* – spolupracujete s kontrakciami, bábätko sa rodí.\n\n"
        "*5. Placenta* – do 30 min po pôrode."
    ),
    "sumka": (
        "🎒 *Čo zbaliť do pôrodnice*\n\n"
        "*Pre mamu:*\n"
        "• Preukaz poistenca + tehotenská knižka\n"
        "• Pohodlná nočná košeľa (2×)\n"
        "• Podprsenka na dojčenie\n"
        "• Papuče, župan\n"
        "• Hygienicke potreby\n"
        "• Nabíjačka na telefón\n\n"
        "*Pre bábätko:*\n"
        "• Body, pyžamko, čiapočka (3–5 ks)\n"
        "• Autosedačka (na cestu domov)\n\n"
        "*Pre partnera:*\n"
        "• Jedlo a pití na noc\n"
        "• Pohodlné oblečenie\n"
        "• Slúchadlá, nabíjačka"
    ),
    "partner": (
        "👨 *Ako môže partner pomôcť*\n\n"
        "• *Byť prítomný* – nemusí nič robiť, stačí byť pri vás\n"
        "• *Dýchanie spolu* – napodobňuje rytmus, pomáha sa sústrediť\n"
        "• *Masáž krížov* – tlak alebo kruhy počas kontrakcie\n"
        "• *Hovoriť ticho* – „Zvládaš to. Som tu.“\n"
        "• *Poznať fázy* – nepanikárí, keď vie čo čakať\n\n"
        "Viac v kurze 👉 magicspace.sk/kurz.html"
    ),
    "kurz": (
        "📚 *Kurz Príprava na pôrod a šestonedelie – Intenzív*\n\n"
        "Online kurz pre páry, celé Slovensko.\n\n"
        "📅 4\\. júla 2025\n"
        "📅 12\\. septembra 2025\n"
        "🕘 9:00 – 17:00\n"
        "💰 59 € / pár\n\n"
        "👉 [Pozrieť kurz](https://magicspace.sk/kurz.html)"
    ),
    "sprievodca": (
        "📄 *Bezplatný sprievodca ku pôrodu*\n\n"
        "Obsahuje fázy pôrodu, dýchacie techniky, vaše práva a šablónu rodového plánu.\n\n"
        "👉 [Stiahnuť zadarmo](https://magicspace.sk/landing.html)"
    ),
    "kontakt": (
        "💌 *Kontakt*\n\n"
        "Anastasia Gamaley\n"
        "Certifikovaná dula · Martin\n\n"
        "✉️ info@magicspace.sk\n"
        "🌐 magicspace.sk"
    ),
    "porodni_plan": (
        "📋 *Rodový plán*\n\n"
        "Rodový plán je krátky dokument, ktorý dávate pôrodnici – hovorí, čo chcete a čo nechcete.\n\n"
        "*Čo do neho patrí:*\n"
        "• Polohy pri pôrode\n"
        "• Postoj k epidurálnej anestézii\n"
        "• Prítomnosť partnera\n"
        "• Kontakt kože na kožu po pôrode\n"
        "• Dojčenie hneď po pôrode\n\n"
        "Šablónu nájdete v bezplatnom sprievodcovi 👉 magicspace.sk/landing.html"
    ),
}

MENU_TEXT = (
    "Vitajte v MagicSpace 🌸\n\n"
    "Som tu, aby som vám pomohla pripraviť sa na pôrod. "
    "Vyberte tému alebo napíšte otázku:\n\n"
    "/fazy – Fázy pôrodu\n"
    "/sumka – Čo zbaliť do pôrodnice\n"
    "/partner – Ako pomôže partner\n"
    "/porodni\\_plan – Rodový plán\n"
    "/kurz – Kurz pre páry (59 €)\n"
    "/sprievodca – Bezplatný sprievodca\n"
    "/kontakt – Kontakt"
)


def send_message(chat_id, text, parse_mode="Markdown"):
    if not BOT_TOKEN:
        return
    try:
        requests.post(f"{TG}/sendMessage", json={
            "chat_id":    chat_id,
            "text":       text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }, timeout=10)
    except Exception as e:
        log.error("TG sendMessage: %s", e)


def handle_update(update: dict):
    """Process one Telegram update (called from /api/telegram-webhook)."""
    msg = update.get("message") or update.get("channel_post")
    if not msg:
        return
    chat_id = msg["chat"]["id"]
    text    = (msg.get("text") or "").strip().lower()

    if text in ("/start", "start"):
        send_message(chat_id, MENU_TEXT)
        return

    cmd = text.lstrip("/").split("@")[0]  # strip bot username if present
    if cmd in FAQ:
        send_message(chat_id, FAQ[cmd])
    else:
        send_message(chat_id, MENU_TEXT)

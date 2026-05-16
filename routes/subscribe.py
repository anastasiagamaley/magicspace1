from flask import Blueprint, request, jsonify
# TODO Step 5: email capture, SQLite storage, GDPR consent, Resend welcome email

subscribe_bp = Blueprint("subscribe", __name__)

@subscribe_bp.route("/api/subscribe", methods=["POST"])
def subscribe():
    # [ ] Step 5 — implement:
    # 1. Validate email + consent (required, not pre-ticked)
    # 2. Honeypot anti-spam check
    # 3. Store in SQLite: email, consent_at, source, language
    # 4. Trigger welcome email via Resend (services/email_resend.py)
    # 5. Return success / already-subscribed
    return jsonify({"ok": False, "error": "Not implemented yet"}), 501

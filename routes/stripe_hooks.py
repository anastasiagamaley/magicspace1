from flask import Blueprint, request, jsonify
# TODO Step 9: receive Stripe webhook, verify signature, deliver product

stripe_hooks_bp = Blueprint("stripe_hooks", __name__)

@stripe_hooks_bp.route("/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    # [ ] Step 9 — implement:
    # 1. Read raw body + Stripe-Signature header
    # 2. Verify signature with stripe.Webhook.construct_event()
    #    — NEVER deliver a product on an unverified webhook
    # 3. On payment_intent.succeeded: look up product in catalogue
    # 4. Deliver: email PDF link (€15) or seminar access details (€60)
    return jsonify({"ok": False, "error": "Not implemented yet"}), 501

import os, stripe
# TODO Step 9: Stripe integration

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    # Raises stripe.error.SignatureVerificationError if invalid
    # NEVER skip this — never deliver a product on an unverified webhook
    return stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)

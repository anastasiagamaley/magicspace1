import os, resend
# TODO Step 6: Resend integration
# [ ] CHECK: SPF / DKIM DNS records must be set up on magicspace.sk before sending

resend.api_key = os.getenv("RESEND_API_KEY", "")

def send_welcome(to_email: str, checklist_url: str, telegram_invite: str):
    # [ ] Step 6 — implement welcome email
    # Sends: pre-birth checklist PDF link + one-time Telegram invite link
    # Template: content/sk/emails/welcome.html
    raise NotImplementedError

def send_nurture(to_email: str, step: int):
    # [ ] Step 8 — implement nurture sequence
    # step 1..4 — loaded from content/sk/emails/nurture_{step}.html
    raise NotImplementedError

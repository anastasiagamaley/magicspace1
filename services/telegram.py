import os, requests
# TODO Step 7: Telegram Bot API — one-time invite links
# [ ] CHECK: create bot via BotFather, make it admin of the private channel

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID  = os.getenv("TELEGRAM_CHANNEL_ID", "")

def create_invite_link() -> str:
    # [ ] Step 7 — implement
    # Calls createChatInviteLink with member_limit=1 so the link works once only
    raise NotImplementedError

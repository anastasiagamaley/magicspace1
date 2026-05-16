# 05 — Email Capture & Nurture (Resend)

**Status:** Not started
*Part of the project documentation. Index: [`00_INDEX.md`](00_INDEX.md).*

---

## Purpose of this file
Email delivery via Resend, the welcome email, and the scripted nurture sequence.

---

## 1. Why Resend
Sending email directly from the VPS via SMTP would land in spam (no sending
reputation). Resend handles deliverability; our code calls its API.
`[ ] CHECK:` Domain authentication (SPF/DKIM DNS records) set up.

## 2. Welcome email
Sent on signup: pre-birth checklist (PDF) + one-time Telegram invite link.

## 3. Nurture sequence
3-5 emails over ~a week, sent by scripts/send_nurture.py via cron.
`[ ] DECISION:` Exact number of emails and day spacing.
Marketing copy MAY be AI-drafted (it is marketing, not medical advice),
but ALL copy is reviewed and approved by the owner. AI is an offline
drafting assistant, never a live generator.

## 4. Templates
All email text in content/sk/emails/ , separate from code.

---

*Stub. Fill in as the project progresses. Resolve every `[ ] CHECK:` and
`[ ] DECISION:` before writing the related code.*

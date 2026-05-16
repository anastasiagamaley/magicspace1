# 04 — Landing Page

**Status:** Not started
*Part of the project documentation. Index: [`00_INDEX.md`](00_INDEX.md).*

---

## Purpose of this file
Structure of the landing page, the email-capture form, and GDPR elements.

---

## 1. Page structure
Single page, one job: exchange the free product for an email.
Headline (promise) -> who (the doula, trust) -> what you get free ->
email form -> Telegram as a bonus -> footer (Privacy Policy, disclaimer).

## 2. The form
Email (required) + consent checkbox (required, NOT pre-ticked — GDPR).
POST to routes/subscribe.py . Server stores record, triggers welcome email.
Basic anti-spam (e.g. honeypot field).

## 3. Email-first principle
Ask email first; Telegram is the bonus. The Telegram channel is not an
owned asset; the email list is.

`[ ] DECISION:` Landing copy must be reviewed against why earlier ads
'did not work' — see 11_financial_model.md and the diagnosis discussion.

---

*Stub. Fill in as the project progresses. Resolve every `[ ] CHECK:` and
`[ ] DECISION:` before writing the related code.*

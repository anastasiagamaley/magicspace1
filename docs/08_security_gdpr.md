# 08 — Security, GDPR & Disclaimers

**Status:** Not started
*Part of the project documentation. Index: [`00_INDEX.md`](00_INDEX.md).*

---

## Purpose of this file
Consent handling, secret management, server hardening, and the 'not medical advice' rule.

---

## 1. GDPR essentials
Consent checkbox, not pre-ticked. A Privacy Policy page. Store consent
timestamp per subscriber. Working unsubscribe in every email.
`[ ] DECISION:` Privacy Policy reviewed by someone qualified.

## 2. Secrets & hardening
API keys in `.env`, never in Git. SSH keys only, password login disabled.
Deploy user with least privilege. Stripe webhook signature verification.
Keep server OS packages updated.

## 3. 'Not medical advice' — hard line
Sensitive, near-medical topic; vulnerable audience. Every product, the
landing page, and the Telegram channel carry a clear disclaimer: this is
informational support from a doula, NOT medical advice, NOT a substitute
for a doctor or midwife. AI never generates medical content. This rule
carries directly into the Roadmap (90).

---

*Stub. Fill in as the project progresses. Resolve every `[ ] CHECK:` and
`[ ] DECISION:` before writing the related code.*

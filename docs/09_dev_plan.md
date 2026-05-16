# 09 — Development Plan (step by step)

**Status:** Not started
*Part of the project documentation. Index: [`00_INDEX.md`](00_INDEX.md).*

---

## Purpose of this file
The build order. Each step produces a working, checkable result before the next begins.

---

Step numbers are an order, not a deadline. The owner has time for
development now; the goal is to save time later.

Step 1 — Verify the server (resolve all `[ ] CHECK:` in 02 and 03).
Step 2 — Infrastructure (SSH keys, deploy user, repo structure).
Step 3 — Deployment pipeline (GitHub Actions; prove with a trivial change).
Step 4 — Landing page (static HTML+CSS, text from content/sk/).
Step 5 — Email capture (form, subscribe route, SQLite, consent).
Step 6 — Resend integration (domain auth, welcome email).
Step 7 — Telegram (bot, private channel, one-time invite links).
Step 8 — Nurture sequence (templates, send_nurture.py, cron).
Step 9 — Product catalogue + Stripe (catalogue as data, webhook, delivery).
Step 10 — Privacy Policy, disclaimers, full end-to-end test.

After Step 10 the funnel is live and self-running. Roadmap (90) only after.

---

*Stub. Fill in as the project progresses. Resolve every `[ ] CHECK:` and
`[ ] DECISION:` before writing the related code.*

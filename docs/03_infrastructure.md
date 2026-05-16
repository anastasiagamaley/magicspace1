# 03 — Infrastructure & Deployment

**Status:** Not started
*Part of the project documentation. Index: [`00_INDEX.md`](00_INDEX.md).*

---

## Purpose of this file
Server hardening and the push-to-deploy pipeline. Must be done before application code is deployed.

---

## 1. SSH — move off passwords
Current: password login. Problem: public servers face constant automated
password-guessing. Target: SSH key pair, install public key, prove key
login works, THEN disable password login.
`[ ] CHECK:` Prove key login works BEFORE disabling passwords (lockout risk).

## 2. Deploy user — least privilege
Do NOT give GitHub Actions the main account. Create a `deploy` user that
can only update site files and restart the service. Its key goes in GitHub
Secrets. Worst-case damage is contained.

## 3. GitHub Actions pipeline
On push to main: (optional checks) -> SSH as `deploy` -> pull -> install
deps -> restart service.
`[ ] CHECK:` Confirm the repository exists and where site code lives.
`[ ] DECISION:` Deploy from `main` or a separate `production` branch.

## 4. Secrets
API keys (Resend, Stripe, Telegram) NEVER committed. Store in `.env` on
the server (in `.gitignore`), load at runtime. Deploy secrets in GitHub Secrets.

---

*Stub. Fill in as the project progresses. Resolve every `[ ] CHECK:` and
`[ ] DECISION:` before writing the related code.*

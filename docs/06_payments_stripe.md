# 06 — Payments (Stripe)

**Status:** Not started
*Part of the project documentation. Index: [`00_INDEX.md`](00_INDEX.md).*

---

## Purpose of this file
Stripe payment, catalogue-driven automatic delivery, and the VAT note.

---

## 1. Approach
Stripe Payment Links / Checkout. Stripe hosts the payment page; our server
never touches card data. No monthly fee — only a % per sale.

## 2. Delivery flow — catalogue-driven
Buyer pays -> Stripe webhook to routes/stripe_hooks.py -> verify webhook
signature -> look up product in the catalogue -> deliver (email file /
access details) per the catalogue row. Works for ANY product, not coded
per-product.
`[ ] CHECK:` Webhook signature verification is mandatory.
`[ ] DECISION:` How to limit sharing of paid download links.

## 3. VAT / invoicing
`[ ] DECISION:` Selling digital products to EU consumers has VAT/invoicing
implications that GROW with the catalogue. Consult an accountant before
sales volume grows. This document does not give tax advice.

---

*Stub. Fill in as the project progresses. Resolve every `[ ] CHECK:` and
`[ ] DECISION:` before writing the related code.*

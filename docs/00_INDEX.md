# Project Design — Digital Product Platform (Birth Preparation)

**Project owner:** Anastasia
**Document status:** Draft v2 — for review
**Last updated:** 2026-05-16
**Working language of these documents:** English (DBD convention).
**Client-facing content language:** Slovak at launch; Russian (for
Russian-speakers across Europe) is a future phase.

---

## What this document is

This is the **index** (umbrella document) for the whole project. It holds
the big picture, the file map, and the status of each part.

**One source of truth — the rule for this documentation.**
Every fact lives in exactly ONE file. Detailed content goes in the
`docs/NN_*.md` files. This index only links to them and shows status. If a
decision is described in `02_architecture.md`, it is NOT re-described here —
only linked. This prevents two copies of a fact drifting apart over time.

This project follows **DBD (Documentation-Based Development)**: the
documentation is written first, the code follows it. Documentation lives in
`docs/` inside the same GitHub repository as the site code, so document and
code are versioned together.

---

## What we are actually building (the frame)

Not "a landing page with a funnel." A **digital product platform** in the
birth-preparation niche.

- The owner's doula expertise is the **content** of the products — not a
  per-hour service being sold.
- This is a deliberate move **away from** competing with other doulas in
  Slovakia (a crowded market that depends on local community presence,
  networking, and constant social visibility — work the owner neither
  enjoys nor has time for).
- The owner's role in the finished system: **invent and author new
  products.** The system does attraction, delivery, payment, and email by
  itself.
- Products are a **growing catalogue.** Electronic products are the core;
  live formats (seminar, personal consultations) sit at the top of the
  price ladder as the human-contact, premium tier.

See `01_overview.md` for the full framing, products, and funnel.

---

## Honest constraints (kept visible on purpose)

These are not problems to hide — they shape every decision below.

1. **Time is the scarcest resource.** The owner has children and a job.
   The whole point of automation is to spend the owner's time only where a
   human is required. The project nonetheless **costs time up front**
   (design, code, first products) and saves time later. Pace must match
   the owner's real available time — see `09_dev_plan.md`.
2. **Competition did not vanish, it moved.** Electronic products do not
   compete with other doulas; they compete for **attention** against free
   content (YouTube, Facebook groups, articles, apps). Differentiation is
   product quality and specificity — see `10_positioning.md`.
3. **"Inventing products" is ongoing real work**, not a one-off. Authoring
   a product well (a sensitive, near-medical topic — no shortcuts) takes
   effort every time. The first few products must exist before the
   platform meaningfully works.
4. **Human contact with buyers is not automated.** Sales and delivery are
   automated; questions, personal messages, and sensitive emails from
   buyers remain the owner's — and on this topic some need real attention.

---

## File map & status

| # | File | Contents | Status |
|---|---|---|---|
| 00 | `00_INDEX.md` | This index | In progress |
| 01 | `01_overview.md` | Frame, products, funnel, languages | Not started |
| 02 | `02_architecture.md` | Flask app, product catalogue as data, i18n, storage | Not started |
| 03 | `03_infrastructure.md` | SSH keys, deploy user, GitHub Actions, secrets | Not started |
| 04 | `04_landing.md` | Landing page structure, form, GDPR | Not started |
| 05 | `05_email_resend.md` | Email capture, Resend, nurture sequence | Not started |
| 06 | `06_payments_stripe.md` | Stripe, catalogue-driven delivery, VAT note | Not started |
| 07 | `07_telegram.md` | Private channel, one-time invite links, bot | Not started |
| 08 | `08_security_gdpr.md` | Consent, secrets, "not medical advice" | Not started |
| 09 | `09_dev_plan.md` | Step-by-step build order | Not started |
| 10 | `10_positioning.md` | What we compete against; differentiation | Not started |
| 11 | `11_financial_model.md` | Honest formula, blank fields for real numbers | Not started |
| 90 | `90_roadmap.md` | Meta ad helper, doula bot — deferred, with risk notes | Not started |

Statuses: `Not started` / `In progress` / `Done`.

---

## How we work with these files

- Each `NN_*.md` file is a stub now: heading, status, back-link to this
  index, and placeholder markers showing exactly where to write.
- We fill files one at a time, in the order of `09_dev_plan.md`.
- Two marker types are used everywhere:
  - `[ ] CHECK:` — a fact about the existing server/site to verify. Never
    guess these.
  - `[ ] DECISION:` — an open product/technical choice still to be made.
- Resolved markers are ticked and the fact written in. Nothing is final
  while markers in the relevant file remain open.

---

## Most urgent open items (blocking everything else)

- `[ ] CHECK:` Server facts — Python version, how Flask runs, nginx, file
  locations, HTTPS, dependencies. See `02_architecture.md` and
  `03_infrastructure.md`. Blocks Step 1 of the dev plan.
- `[ ] CHECK:` GitHub repository exists and where the site code lives.
- `[ ] DECISION:` Subscriber data storage — recommendation: SQLite. See
  `02_architecture.md`.

---

*End of index v2. Update statuses as files are filled.*

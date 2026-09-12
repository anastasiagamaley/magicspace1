# Security hotfix: root static file disclosure

## What was fixed

`app.py` constructed Flask with `static_folder=BASE, static_url_path=""`,
which registers an implicit catch-all route serving **any file in the
project root** at the site root (e.g. `/app.py`, `/.env`, `/magicspace.db`).
That exposed source code, admin password / mail credentials, and the
SQLite database over HTTP.

Fix, entirely in `app.py`:

- `Flask(__name__, static_folder=None)` — removes the catch-all static route.
- New `/<filename>` route backed by an explicit `PUBLIC_ROOT_FILES`
  allowlist (`api.js`, `favicon.png`, `magicspace_leadmagnet.pdf`,
  `byt_tam_paid_guide.pdf`), each served with an explicit mimetype. Anything
  not in the allowlist 404s, regardless of what's on disk.
- `/<page>.html` now validates `page` against `PAGE_NAME_RE`
  (`^[a-zA-Z0-9_-]+$`) before touching the filesystem. Existing behavior is
  otherwise unchanged, so server-only HTML pages that aren't in this repo
  (e.g. `landing.html`, `kurz.html`, `magicspace_leadmagnet.html`) keep
  working exactly as before.
- `/uploads/<filename>`, `/sitemap.xml`, `/robots.txt`, and `/jogamartin`
  routes are untouched.

## Emergency layer already in place

An nginx-level rule blocking direct access to `.py`, `.db`, and `.env` at
the root was already deployed ahead of this code fix as a stopgap. This
patch is the underlying application-level fix; the nginx rule can stay as
defense in depth.

## Residual work: credential rotation required

Because the leak was live in production before the nginx stopgap went in,
treat all secrets readable from `.env` (`ADMIN_PASSWORD`, `MAIL_USER`/
`MAIL_PASS`, session `.secret_key`) as potentially exposed and **rotate
them**. This patch does not rotate anything — it only stops future
disclosure.

## Out of scope

- Paid PDF link-sharing behavior (`magicspace_leadmagnet.pdf`,
  `byt_tam_paid_guide.pdf` are intentionally public-by-URL, unchanged) —
  no signed-URL/auth gating was added.
- No funnel, auth, or payment logic was touched.
- This release excludes the in-development funnel work; only the static
  file disclosure is fixed here.

## Tests

`tests/test_static_security.py` extracts just the Flask app construction
and static-routing functions out of `app.py` via `ast` (never imports
`app.py` directly, since that would open a live DB connection and start
the APScheduler background scheduler) and runs them against a throwaway
tempdir of dummy files/secrets. All nine tests pass against the fixed version.
The test harness rejects the pre-fix routing shape because the allowlist is
missing; that alone is not a behavioral regression proof. An independent
isolated check also extracted the original and patched routes and verified
`/.env` and `/.git/config` return 200 before the fix and 404 after it, while
`/` remains 200. Only dummy temporary files were used; the full application
was never imported for these checks.

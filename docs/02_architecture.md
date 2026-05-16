# 02 — Architecture

**Status:** Not started
*Part of the project documentation. Index: [`00_INDEX.md`](00_INDEX.md).*

---

## Purpose of this file
How the existing Flask site is structured and what we add. The product catalogue as DATA (not code) is the central element.

---

## 1. Existing site — TO VERIFY
A Flask 'business card' site (yoga + doula, event registration) already exists.
`[ ] CHECK:` Python version on server (`python3 --version`).
`[ ] CHECK:` How Flask runs — gunicorn? systemd? bare `flask run`?
`[ ] CHECK:` Is nginx (or other web server) in front?
`[ ] CHECK:` Where site files live on disk.
`[ ] CHECK:` Is HTTPS/TLS already configured?
`[ ] CHECK:` Is there a `requirements.txt`?

## 2. Target structure
TODO: project layout — routes/, services/, content/sk/, scripts/, etc.
We extend the existing Flask app, no second framework.

## 3. Product catalogue as DATA — central design choice
Because the owner's role is 'invent new products', adding a product must
NOT require a developer. Products live in a catalogue (table/file): name,
price, type, file to deliver, email text. One generic mechanism serves any
product. New product = new row + uploaded file. Same principle as i18n.
`[ ] DECISION:` Catalogue format — SQLite table vs. structured file.

## 4. i18n-ready
All client-facing text in content/sk/ , separate from code. Adding Russian
later = add content/ru/ . No hard-coded strings in Python/HTML.

## 5. Data storage
`[ ] DECISION:` Subscriber storage — recommendation: SQLite (single file,
no extra server, right for a small VPS).

---

*Stub. Fill in as the project progresses. Resolve every `[ ] CHECK:` and
`[ ] DECISION:` before writing the related code.*

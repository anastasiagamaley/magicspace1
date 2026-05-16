# 90 — Roadmap — Future (NOT built now)

**Status:** Not started
*Part of the project documentation. Index: [`00_INDEX.md`](00_INDEX.md).*

---

## Purpose of this file
Deferred items. Recorded so the current architecture does not block them — not work for this phase.

---

## 90.1 Meta advertising helper
Goal: reduce the manual work of running Meta ads.
Risk: a fully autonomous agent that spends real ad money unattended is the
highest-risk part of the project — a bug can drain the budget. Meta also
restricts automated ad-account control and bans suspicious automation.
Realistic direction: NOT 'an agent that decides everything', but a helper
script that collects stats and sends the owner a summary with suggestions
— the owner presses the buttons.
PREREQUISITE: first diagnose why earlier ads failed and find a working
ad->landing->signup->sale chain on a small test (see 10_positioning.md).
Automating advertising that does not work just spends budget faster.

## 90.2 Doula bot (paid subscription)
Goal: a bot answering pregnant clients' questions, funded by subscription.
SERIOUS RISK: a bot giving health-related advice to pregnant women, around
the clock, is NOT the same as a bot handing out invite links. Scenario: at
3 a.m. a pregnant woman messages about pain; if the bot reassures her and
it was actually urgent, consequences can be severe and liability falls on
the service owner. A paid subscription deepens this.
REQUIREMENTS before this is ever built — a SEPARATE project with its own
design and risk review:
- hard boundaries: the bot NEVER assesses symptoms or reassures on medical
  concerns; on anything worrying it directs to a doctor / emergency care;
- explicit, prominent disclaimers;
- legal advice on liability before launch.
Marked 'requires its own design and risk assessment'. Out of scope until
that separate work is done.

---

*Stub. Fill in as the project progresses. Resolve every `[ ] CHECK:` and
`[ ] DECISION:` before writing the related code.*

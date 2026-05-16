#!/usr/bin/env python3
"""
Nurture sequence sender — run by cron on the server.
Finds subscribers due for the next nurture email and sends it.

Cron example (runs daily at 09:00):
  0 9 * * * /usr/bin/python3 /var/www/magicspace/scripts/send_nurture.py

TODO Step 8 — implement:
1. Query data/subscribers.db for rows where next_nurture_at <= now
2. For each: call services.email_resend.send_nurture(email, step)
3. Update next_nurture_at and nurture_step in DB
4. Log sent/failed
"""
# [ ] DECISION: exact number of emails and day spacing (see 05_email_resend.md)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    raise NotImplementedError("Step 8 not implemented yet")

if __name__ == "__main__":
    main()

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db import SessionLocal
from app.models import AlertRecipient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--person-id", type=int, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", default="")
    parser.add_argument("--phone", default="")
    parser.add_argument("--send-email", action="store_true")
    parser.add_argument("--send-sms", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        row = AlertRecipient(
            person_id=args.person_id,
            name=args.name.strip(),
            email=args.email.strip() or None,
            phone_e164=args.phone.strip() or None,
            send_email=args.send_email,
            send_sms=args.send_sms,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        print(f"Created alert recipient {row.id} for person {row.person_id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

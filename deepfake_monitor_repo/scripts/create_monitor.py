import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db import SessionLocal
from app.models import MonitoredPerson


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--aliases", default="")
    parser.add_argument("--reference-accounts", default="")
    parser.add_argument("--reference-images", default="")
    parser.add_argument("--reference-audio", default="")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        row = MonitoredPerson(
            full_name=args.name.strip(),
            aliases=[x.strip() for x in args.aliases.split(",") if x.strip()],
            reference_accounts=[x.strip() for x in args.reference_accounts.split(",") if x.strip()],
            reference_image_paths=[x.strip() for x in args.reference_images.split(",") if x.strip()],
            reference_audio_paths=[x.strip() for x in args.reference_audio.split(",") if x.strip()],
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        print(f"Created monitor {row.id} for {row.full_name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

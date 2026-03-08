import argparse
from app.crud import upsert_single_profile
from app.db import SessionLocal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--alias", action="append", default=[])
    parser.add_argument("--handle", action="append", default=[])
    parser.add_argument("--description", default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        profile = upsert_single_profile(db, args.name, args.alias, args.handle, args.description)
        print(f"Profile ready: {profile.id} {profile.full_name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""Generate daily_challenges entries for a given year.

Usage: uv run python scripts/generate_challenges.py --year 2026
"""
import argparse
import random
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import supabase

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()

    people = supabase.table("people").select("id").execute().data
    if not people:
        print("Error: No people in database. Run seed_people.py first.")
        return

    print(f"Found {len(people)} people in database")

    year_start = date(args.year, 1, 1)
    year_end = date(args.year, 12, 31)
    existing = supabase.table("daily_challenges").select("date").gte(
        "date", str(year_start)
    ).lte("date", str(year_end)).execute()
    existing_dates = {row["date"] for row in existing.data}
    print(f"Found {len(existing_dates)} existing challenges for {args.year}")

    rng = random.Random(args.year)
    person_ids = [p["id"] for p in people]
    rng.shuffle(person_ids)

    current = year_start
    idx = 0
    new_challenges = []
    while current <= year_end:
        if str(current) not in existing_dates:
            new_challenges.append({
                "date": str(current),
                "person_id": person_ids[idx % len(person_ids)],
            })
        idx += 1
        current += timedelta(days=1)

    if not new_challenges:
        print("All dates already have challenges. Nothing to do.")
        return

    for i in range(0, len(new_challenges), 50):
        batch = new_challenges[i:i+50]
        supabase.table("daily_challenges").insert(batch).execute()
        print(f"  Inserted batch {i//50 + 1} ({len(batch)} challenges)")

    print(f"Generated {len(new_challenges)} new challenges for {args.year}")

if __name__ == "__main__":
    main()

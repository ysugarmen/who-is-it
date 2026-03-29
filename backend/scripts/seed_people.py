"""Fetch famous people from Wikidata and seed the people table in Supabase.

Usage: uv run python scripts/seed_people.py --count 400
"""
import argparse
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import supabase

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

SPARQL_QUERY = """
SELECT DISTINCT ?person ?personLabel ?image ?occupation ?occupationLabel WHERE {{
  ?person wdt:P31 wd:Q5 .
  ?person wdt:P18 ?image .
  ?person wdt:P106 ?occupation .
  ?occupation wdt:P279* wd:Q2066131 .
  ?person wikibase:sitelinks ?sitelinks .
  FILTER(?sitelinks > 40)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
ORDER BY DESC(?sitelinks)
LIMIT {limit}
"""

CATEGORY_MAP = {
    "actor": ["actor", "actress", "film actor", "television actor", "voice actor"],
    "musician": ["singer", "musician", "rapper", "composer", "songwriter", "guitarist"],
    "athlete": ["athlete", "footballer", "basketball player", "tennis player", "boxer"],
    "politician": ["politician", "head of state", "president", "prime minister"],
}

def classify_category(occupation: str) -> str:
    occupation_lower = occupation.lower()
    for category, keywords in CATEGORY_MAP.items():
        if any(kw in occupation_lower for kw in keywords):
            return category
    return "other"

def fetch_people(limit: int) -> list[dict]:
    query = SPARQL_QUERY.format(limit=limit)
    resp = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": "WhoIsIt-Game/1.0"},
    )
    resp.raise_for_status()
    results = resp.json()["results"]["bindings"]

    seen = set()
    people = []
    for row in results:
        name = row["personLabel"]["value"]
        if name in seen:
            continue
        seen.add(name)
        image_url = row["image"]["value"]
        if "commons.wikimedia.org" not in image_url:
            continue
        category = classify_category(row.get("occupationLabel", {}).get("value", ""))
        people.append({
            "name": name,
            "aliases": [],
            "image_url": image_url,
            "category": category,
            "license": "CC-BY-SA",
            "attribution_url": image_url,
        })
    return people

def seed_database(people: list[dict]):
    for i in range(0, len(people), 50):
        batch = people[i:i+50]
        supabase.table("people").upsert(batch, on_conflict="name").execute()
        print(f"  Inserted batch {i//50 + 1} ({len(batch)} people)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=400)
    args = parser.parse_args()

    print(f"Fetching {args.count} famous people from Wikidata...")
    people = fetch_people(args.count)
    print(f"Found {len(people)} people with valid images")

    print("Seeding database...")
    seed_database(people)
    print("Done!")

if __name__ == "__main__":
    main()

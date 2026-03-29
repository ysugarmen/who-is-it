from datetime import date, timezone, datetime
from app.db import supabase

def get_today_utc() -> date:
    return datetime.now(timezone.utc).date()

def get_todays_challenge() -> dict | None:
    today = get_today_utc()
    result = supabase.table("daily_challenges").select(
        "date, person_id, people(name, image_url, category, aliases)"
    ).eq("date", str(today)).execute()
    if not result.data:
        return None
    row = result.data[0]
    person = row["people"]
    return {
        "date": row["date"],
        "image_url": person["image_url"],
        "category": person["category"],
        "person_id": row["person_id"],
        "name": person["name"],
        "aliases": person["aliases"],
    }

def get_player_game_state(player_id: str, challenge_date: date) -> dict | None:
    result = supabase.table("game_results").select("*").eq(
        "player_id", player_id
    ).eq("date", str(challenge_date)).execute()
    if not result.data:
        return None
    return result.data[0]

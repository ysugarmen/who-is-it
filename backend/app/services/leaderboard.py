from datetime import date, datetime, timezone, timedelta
from app.db import supabase

def get_today_utc() -> date:
    return datetime.now(timezone.utc).date()

def get_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())

def get_leaderboard(view: str, player_id: str | None = None) -> dict:
    if view == "daily":
        return _daily_leaderboard(player_id)
    elif view == "weekly":
        return _weekly_leaderboard(player_id)
    elif view == "alltime":
        return _alltime_leaderboard(player_id)
    raise ValueError(f"Invalid view: {view}")

def _daily_leaderboard(player_id: str | None) -> dict:
    today = get_today_utc()
    results = supabase.table("game_results").select(
        "player_id, guesses_used, solved, players(nickname)"
    ).eq("date", str(today)).eq("solved", True).order(
        "guesses_used", desc=False
    ).limit(50).execute()

    entries = []
    for i, row in enumerate(results.data):
        points = 8 - row["guesses_used"]
        entries.append({
            "rank": i + 1,
            "nickname": row["players"]["nickname"],
            "points": points,
            "guesses_used": row["guesses_used"],
        })

    player_rank = _find_player_rank_daily(player_id, today, entries) if player_id else None
    return {"entries": entries, "player_rank": player_rank}

def _weekly_leaderboard(player_id: str | None) -> dict:
    today = get_today_utc()
    week_start = get_week_start(today)
    week_end = week_start + timedelta(days=6)

    results = supabase.rpc("weekly_leaderboard", {
        "week_start": str(week_start),
        "week_end": str(week_end),
    }).execute()

    entries = []
    for i, row in enumerate(results.data[:50]):
        entries.append({
            "rank": i + 1,
            "nickname": row["nickname"],
            "points": row["total_points"],
        })

    player_rank = _find_player_in_entries(player_id, results.data, entries) if player_id else None
    return {"entries": entries, "player_rank": player_rank}

def _alltime_leaderboard(player_id: str | None) -> dict:
    results = supabase.table("players").select(
        "id, nickname, total_points, longest_streak"
    ).order("total_points", desc=True).limit(50).execute()

    entries = []
    for i, row in enumerate(results.data):
        entries.append({
            "rank": i + 1,
            "nickname": row["nickname"],
            "points": row["total_points"],
        })

    player_rank = None
    if player_id:
        in_top = any(row["id"] == player_id for row in results.data)
        if not in_top:
            player_data = supabase.table("players").select(
                "nickname, total_points"
            ).eq("id", player_id).execute()
            if player_data.data:
                p = player_data.data[0]
                count = supabase.table("players").select(
                    "id", count="exact"
                ).gt("total_points", p["total_points"]).execute()
                player_rank = {
                    "rank": (count.count or 0) + 1,
                    "nickname": p["nickname"],
                    "points": p["total_points"],
                }

    return {"entries": entries, "player_rank": player_rank}

def _find_player_rank_daily(player_id: str, today: date, top_entries: list) -> dict | None:
    player_result = supabase.table("game_results").select(
        "guesses_used, players(nickname)"
    ).eq("player_id", player_id).eq("date", str(today)).eq("solved", True).execute()

    if not player_result.data:
        return None

    nickname = player_result.data[0]["players"]["nickname"]
    if any(e["nickname"] == nickname for e in top_entries):
        return None

    guesses = player_result.data[0]["guesses_used"]
    points = 8 - guesses
    count = supabase.table("game_results").select(
        "id", count="exact"
    ).eq("date", str(today)).eq("solved", True).lt("guesses_used", guesses).execute()

    return {
        "rank": (count.count or 0) + 1,
        "nickname": nickname,
        "points": points,
        "guesses_used": guesses,
    }

def _find_player_in_entries(player_id: str, all_data: list, top_entries: list) -> dict | None:
    for i, row in enumerate(all_data):
        if row.get("player_id") == player_id and i >= 50:
            return {
                "rank": i + 1,
                "nickname": row["nickname"],
                "points": row["total_points"],
            }
    return None

from app.db import supabase

def create_player(nickname: str) -> dict:
    existing = supabase.table("players").select("id").eq("nickname", nickname).execute()
    if existing.data:
        raise ValueError(f"Nickname '{nickname}' is already taken")
    result = supabase.table("players").insert({"nickname": nickname}).execute()
    return result.data[0]

def get_player_stats(player_id: str) -> dict:
    result = supabase.table("players").select(
        "nickname, total_points, current_streak, longest_streak"
    ).eq("id", player_id).execute()
    if not result.data:
        raise ValueError("Player not found")
    player = result.data[0]
    count = supabase.table("players").select(
        "id", count="exact"
    ).gt("total_points", player["total_points"]).execute()
    player["rank"] = (count.count or 0) + 1
    return player

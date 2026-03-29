from thefuzz import fuzz
from datetime import date, timezone, datetime
from app.db import supabase
from app.config import settings

def is_correct_guess(guess: str, name: str, aliases: list[str]) -> bool:
    threshold = settings.fuzzy_match_threshold
    candidates = [name] + aliases
    for candidate in candidates:
        if fuzz.ratio(guess.lower().strip(), candidate.lower().strip()) >= threshold:
            return True
    return False

def calculate_points(guesses_used: int) -> int:
    if guesses_used == 0:
        return 0
    return 8 - guesses_used

def process_guess(player_id: str, guess: str, challenge_date: date) -> dict:
    today = datetime.now(timezone.utc).date()
    if challenge_date != today:
        raise ValueError("Can only guess for today's challenge")

    challenge = supabase.table("daily_challenges").select(
        "person_id, people(name, aliases)"
    ).eq("date", str(challenge_date)).execute()
    if not challenge.data:
        raise ValueError("No challenge for this date")

    person = challenge.data[0]["people"]
    person_name = person["name"]
    aliases = person["aliases"]

    existing = supabase.table("game_results").select("*").eq(
        "player_id", player_id
    ).eq("date", str(challenge_date)).execute()

    if existing.data:
        game = existing.data[0]
        if game["solved"] or game["guesses_used"] >= 7:
            raise ValueError("Game already completed for today")
        guesses = game["guesses"]
        guesses_used = game["guesses_used"]
    else:
        guesses = []
        guesses_used = 0

    correct = is_correct_guess(guess, person_name, aliases)
    guesses.append(guess)
    guesses_used += 1
    game_over = correct or guesses_used >= 7

    row = {
        "player_id": player_id,
        "date": str(challenge_date),
        "guesses_used": guesses_used,
        "solved": correct,
        "guesses": guesses,
    }

    if existing.data:
        supabase.table("game_results").update(row).eq(
            "id", existing.data[0]["id"]
        ).execute()
    else:
        supabase.table("game_results").insert(row).execute()

    if game_over and correct:
        points = calculate_points(guesses_used)
        player = supabase.table("players").select("*").eq("id", player_id).execute().data[0]
        yesterday = date.fromordinal(challenge_date.toordinal() - 1)
        yesterday_result = supabase.table("game_results").select("solved").eq(
            "player_id", player_id
        ).eq("date", str(yesterday)).execute()
        yesterday_solved = yesterday_result.data and yesterday_result.data[0]["solved"]

        new_streak = (player["current_streak"] + 1) if yesterday_solved else 1
        longest = max(player["longest_streak"], new_streak)

        supabase.table("players").update({
            "total_points": player["total_points"] + points,
            "current_streak": new_streak,
            "longest_streak": longest,
        }).eq("id", player_id).execute()
    elif game_over and not correct:
        supabase.table("players").update({
            "current_streak": 0,
        }).eq("id", player_id).execute()

    result = {
        "correct": correct,
        "guesses_remaining": 7 - guesses_used,
    }
    if game_over:
        result["answer"] = person_name
    return result

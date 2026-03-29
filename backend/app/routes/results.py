from fastapi import APIRouter, HTTPException, Depends
from datetime import date
from app.models import GameResultResponse
from app.services.guess import calculate_points
from app.auth import get_player_required
from app.db import supabase

router = APIRouter(prefix="/api")

@router.get("/results/{result_date}", response_model=GameResultResponse)
def get_result(result_date: date, player=Depends(get_player_required)):
    result = supabase.table("game_results").select("*").eq(
        "player_id", player["id"]
    ).eq("date", str(result_date)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No result for this date")
    game = result.data[0]
    points = calculate_points(game["guesses_used"]) if game["solved"] else 0
    return GameResultResponse(
        date=game["date"],
        guesses_used=game["guesses_used"],
        solved=game["solved"],
        guesses=game["guesses"],
        points=points,
    )

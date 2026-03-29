from fastapi import APIRouter, HTTPException, Depends, Query
from app.models import LeaderboardResponse
from app.services.leaderboard import get_leaderboard
from app.auth import get_player_optional

router = APIRouter(prefix="/api")

@router.get("/leaderboard", response_model=LeaderboardResponse)
def leaderboard(
    view: str = Query(pattern="^(daily|weekly|alltime)$"),
    player=Depends(get_player_optional),
):
    player_id = player["id"] if player else None
    try:
        result = get_leaderboard(view, player_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return LeaderboardResponse(**result)

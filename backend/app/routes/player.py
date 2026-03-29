from fastapi import APIRouter, HTTPException, Depends
from app.models import CreatePlayerRequest, PlayerResponse, PlayerStatsResponse
from app.services.player import create_player, get_player_stats
from app.auth import get_player_required

router = APIRouter(prefix="/api")

@router.post("/player", response_model=PlayerResponse)
def register_player(req: CreatePlayerRequest):
    try:
        player = create_player(req.nickname)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return PlayerResponse(token=str(player["token"]), player_id=str(player["id"]))

@router.get("/player/me", response_model=PlayerStatsResponse)
def get_my_stats(player=Depends(get_player_required)):
    stats = get_player_stats(player["id"])
    return PlayerStatsResponse(**stats)

from fastapi import APIRouter, HTTPException, Depends
from app.models import GuessRequest, GuessResponse
from app.services.guess import process_guess
from app.auth import get_player_required

router = APIRouter(prefix="/api")

@router.post("/guess", response_model=GuessResponse)
def submit_guess(req: GuessRequest, player=Depends(get_player_required)):
    try:
        result = process_guess(player["id"], req.guess, req.date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return GuessResponse(**result)

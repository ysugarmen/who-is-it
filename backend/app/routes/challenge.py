from fastapi import APIRouter, HTTPException, Depends
from app.models import ChallengeResponse
from app.services.challenge import get_todays_challenge, get_player_game_state
from app.auth import get_player_optional

router = APIRouter(prefix="/api")

@router.get("/challenge/today", response_model=ChallengeResponse)
def today_challenge(player=Depends(get_player_optional)):
    challenge = get_todays_challenge()
    if not challenge:
        raise HTTPException(status_code=404, detail="No challenge for today")

    response = ChallengeResponse(
        date=challenge["date"],
        image_url=challenge["image_url"],
        category=challenge["category"],
    )

    if player:
        game_state = get_player_game_state(player["id"], challenge["date"])
        if game_state:
            response.guesses_used = game_state["guesses_used"]
            response.solved = game_state["solved"]
            response.guesses = game_state["guesses"]
            if game_state["solved"] or game_state["guesses_used"] >= 7:
                response.answer = challenge["name"]

    return response

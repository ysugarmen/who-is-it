from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="Who Is It?")

from app.routes.player import router as player_router
app.include_router(player_router)

from app.routes.challenge import router as challenge_router
app.include_router(challenge_router)

from app.routes.guess import router as guess_router
app.include_router(guess_router)

from app.routes.leaderboard import router as leaderboard_router
from app.routes.results import router as results_router
app.include_router(leaderboard_router)
app.include_router(results_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

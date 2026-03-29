from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.config import settings
import httpx

app = FastAPI(title="Who Is It?")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes.player import router as player_router
from app.routes.challenge import router as challenge_router
from app.routes.guess import router as guess_router
from app.routes.leaderboard import router as leaderboard_router
from app.routes.results import router as results_router

app.include_router(player_router)
app.include_router(challenge_router)
app.include_router(guess_router)
app.include_router(leaderboard_router)
app.include_router(results_router)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/image-proxy")
async def image_proxy(url: str = Query(...)):
    if "wikimedia.org" not in url and "wikipedia.org" not in url:
        return Response(status_code=400, content="Only Wikimedia URLs allowed")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url)
    return Response(
        content=resp.content,
        media_type=resp.headers.get("content-type", "image/jpeg"),
        headers={"Cache-Control": "public, max-age=86400"},
    )

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

# -- Requests --
class CreatePlayerRequest(BaseModel):
    nickname: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")

class GuessRequest(BaseModel):
    guess: str = Field(min_length=1)
    date: date

# -- Responses --
class PlayerResponse(BaseModel):
    token: str
    player_id: str

class PlayerStatsResponse(BaseModel):
    nickname: str
    total_points: int
    current_streak: int
    longest_streak: int
    rank: int

class ChallengeResponse(BaseModel):
    date: date
    image_url: str
    category: Optional[str] = None
    guesses_used: Optional[int] = None
    solved: Optional[bool] = None
    guesses: Optional[list[str]] = None
    answer: Optional[str] = None

class GuessResponse(BaseModel):
    correct: bool
    guesses_remaining: int
    answer: Optional[str] = None

class LeaderboardEntry(BaseModel):
    rank: int
    nickname: str
    points: int
    guesses_used: Optional[int] = None

class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    player_rank: Optional[LeaderboardEntry] = None

class GameResultResponse(BaseModel):
    date: date
    guesses_used: int
    solved: bool
    guesses: list[str]
    points: int

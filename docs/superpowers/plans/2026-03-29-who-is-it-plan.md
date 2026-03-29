# Who Is It? Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily pixelated celebrity guessing game with leaderboards, deployed on free-tier hosting.

**Architecture:** FastAPI backend (Render) + React/Vite frontend (Vercel) + Supabase (PostgreSQL + Storage). Backend handles guess validation via fuzzy matching, daily challenge serving, and leaderboard queries. Frontend handles pixelation via Canvas API and all game UI.

**Tech Stack:** Python/FastAPI, React/Vite/TypeScript, Supabase, thefuzz, Canvas API

**Spec:** `docs/superpowers/specs/2026-03-29-who-is-it-design.md`

---

## File Structure

### Backend (`backend/`)
```
backend/
├── pyproject.toml              # uv project config, dependencies
├── .env.example                # Template for env vars (SUPABASE_URL, SUPABASE_KEY)
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, lifespan
│   ├── config.py               # Settings via pydantic-settings
│   ├── auth.py                 # Token extraction + player lookup dependency
│   ├── models.py               # Pydantic schemas for request/response
│   ├── db.py                   # Supabase client singleton
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── player.py           # POST /api/player
│   │   ├── challenge.py        # GET /api/challenge/today
│   │   ├── guess.py            # POST /api/guess
│   │   ├── leaderboard.py      # GET /api/leaderboard
│   │   └── results.py          # GET /api/results/{date}, GET /api/player/me
│   └── services/
│       ├── __init__.py
│       ├── challenge.py        # Get today's challenge from daily_challenges
│       ├── guess.py            # Fuzzy match logic, scoring, streak update
│       ├── player.py           # Create player, get stats
│       └── leaderboard.py      # Leaderboard queries (daily/weekly/alltime)
├── scripts/
│   ├── seed_people.py          # Wikidata fetch + Supabase upload
│   └── generate_challenges.py  # Seeded PRNG to fill daily_challenges table
└── tests/
    ├── conftest.py             # Shared fixtures
    ├── test_guess_service.py   # Fuzzy matching + scoring logic
    ├── test_player_service.py  # Player creation + stats
    ├── test_challenge_service.py # Challenge retrieval
    ├── test_routes.py          # API integration tests
    └── test_leaderboard.py     # Leaderboard query tests
```

### Frontend (`frontend/`)
```
frontend/
├── package.json
├── vite.config.ts
├── index.html
├── public/
├── src/
│   ├── main.tsx                # React entry point
│   ├── App.tsx                 # Router setup
│   ├── api.ts                  # Axios instance + API functions
│   ├── types.ts                # TypeScript interfaces
│   ├── hooks/
│   │   ├── useGame.ts          # Game state management (guesses, round, solved)
│   │   ├── usePlayer.ts        # Player auth (token, nickname, stats)
│   │   └── useCountdown.ts     # Countdown timer to UTC midnight
│   ├── components/
│   │   ├── PixelImage.tsx      # Canvas-based pixelation component
│   │   ├── GuessInput.tsx      # Text input + guess button
│   │   ├── GuessIndicators.tsx # 7 slots showing guess status
│   │   ├── GuessList.tsx       # Previous wrong guesses
│   │   ├── Header.tsx          # Logo, streak, leaderboard link
│   │   ├── NicknameModal.tsx   # First-visit nickname prompt
│   │   ├── ResultScreen.tsx    # Win/lose screen with stats + share
│   │   ├── ShareButton.tsx     # Copy result to clipboard
│   │   └── Countdown.tsx       # Next challenge countdown
│   ├── pages/
│   │   ├── GamePage.tsx        # Main game page (composes game components)
│   │   └── LeaderboardPage.tsx # Leaderboard with tabs
│   └── styles/
│       └── global.css          # Dark theme, layout, typography
```

### Database (`database/`)
```
database/
└── schema.sql                  # All CREATE TABLE statements + indexes
```

---

## Chunk 1: Backend Foundation

### Task 1: Project Setup + Database Schema

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/db.py`
- Create: `backend/app/main.py`
- Create: `backend/.env.example`
- Create: `database/schema.sql`

- [ ] **Step 1: Create backend project with uv**

```bash
cd whoIsIt
mkdir -p backend/app backend/app/routes backend/app/services backend/tests database
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "who-is-it-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "supabase>=2.0.0",
    "thefuzz[speedup]>=0.22.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 3: Install dependencies**

```bash
cd backend && uv sync --all-extras
```

- [ ] **Step 4: Create database schema**

Write `database/schema.sql`:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    image_url TEXT NOT NULL,
    category TEXT,
    license TEXT,
    attribution_url TEXT,
    UNIQUE(name)
);

CREATE TABLE daily_challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL UNIQUE,
    person_id UUID NOT NULL REFERENCES people(id)
);

CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nickname TEXT NOT NULL UNIQUE,
    token UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    total_points INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE game_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id),
    date DATE NOT NULL,
    guesses_used INT NOT NULL,
    solved BOOLEAN NOT NULL DEFAULT false,
    guesses TEXT[] NOT NULL DEFAULT '{}',
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(player_id, date)
);

CREATE INDEX idx_game_results_date ON game_results(date);
CREATE INDEX idx_game_results_player_date ON game_results(player_id, date);
CREATE INDEX idx_daily_challenges_date ON daily_challenges(date);
CREATE INDEX idx_players_token ON players(token);
CREATE INDEX idx_players_total_points ON players(total_points DESC);
```

- [ ] **Step 5: Create .env.example**

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
CORS_ORIGINS=http://localhost:5173
FUZZY_MATCH_THRESHOLD=85
```

- [ ] **Step 6: Create config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    cors_origins: str = "http://localhost:5173"
    fuzzy_match_threshold: int = 85

    model_config = {"env_file": ".env"}

settings = Settings()
```

- [ ] **Step 7: Create db.py**

```python
from supabase import create_client, Client
from app.config import settings

def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)

supabase: Client = get_supabase()
```

- [ ] **Step 8: Create main.py with CORS**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="Who Is It?")

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
```

- [ ] **Step 9: Create empty __init__.py files**

Create `backend/app/__init__.py`, `backend/app/routes/__init__.py`, `backend/app/services/__init__.py`.

- [ ] **Step 10: Verify server starts**

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
# Visit http://localhost:8000/api/health → {"status": "ok"}
```

- [ ] **Step 11: Commit**

```bash
git add backend/ database/
git commit -m "feat: backend project setup with FastAPI, Supabase config, and DB schema"
```

---

### Task 2: Pydantic Models + Auth Dependency

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/auth.py`

- [ ] **Step 1: Create models.py**

```python
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
    # Included if player has an in-progress or completed game today
    guesses_used: Optional[int] = None
    solved: Optional[bool] = None
    guesses: Optional[list[str]] = None
    answer: Optional[str] = None  # Only if game is over

class GuessResponse(BaseModel):
    correct: bool
    guesses_remaining: int
    answer: Optional[str] = None  # Only when game is over

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
```

- [ ] **Step 2: Create auth.py**

```python
from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.db import supabase

async def get_player_optional(authorization: Optional[str] = Header(None)):
    """Returns player dict or None if no token provided."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    result = supabase.table("players").select("*").eq("token", token).execute()
    if not result.data:
        return None
    return result.data[0]

async def get_player_required(authorization: str = Header(...)):
    """Returns player dict or raises 401."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    result = supabase.table("players").select("*").eq("token", token).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return result.data[0]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models.py backend/app/auth.py
git commit -m "feat: add Pydantic models and auth dependencies"
```

---

### Task 3: Player Service + Route

**Files:**
- Create: `backend/app/services/player.py`
- Create: `backend/app/routes/player.py`
- Create: `backend/tests/test_player_service.py`

- [ ] **Step 1: Write failing test for player creation**

`backend/tests/test_player_service.py`:

```python
import pytest
from unittest.mock import MagicMock, patch

from app.services.player import create_player, get_player_stats

def test_create_player_valid_nickname():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "uuid-1", "token": "token-1", "nickname": "test_user"}
    ]
    with patch("app.services.player.supabase", mock_supabase):
        result = create_player("test_user")
    assert result["nickname"] == "test_user"
    assert "token" in result

def test_create_player_duplicate_nickname():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "existing", "nickname": "taken"}
    ]
    with patch("app.services.player.supabase", mock_supabase):
        with pytest.raises(ValueError, match="already taken"):
            create_player("taken")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/test_player_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.player'`

- [ ] **Step 3: Write player service**

`backend/app/services/player.py`:

```python
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
    # Calculate rank
    count = supabase.table("players").select(
        "id", count="exact"
    ).gt("total_points", player["total_points"]).execute()
    player["rank"] = (count.count or 0) + 1
    return player
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/test_player_service.py -v
```

Expected: PASS

- [ ] **Step 5: Write player route**

`backend/app/routes/player.py`:

```python
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
```

- [ ] **Step 6: Register route in main.py**

Add to `backend/app/main.py`:

```python
from app.routes.player import router as player_router
app.include_router(player_router)
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/player.py backend/app/routes/player.py backend/tests/test_player_service.py backend/app/main.py backend/app/services/__init__.py
git commit -m "feat: add player registration and stats endpoints"
```

---

### Task 4: Challenge Service + Route

**Files:**
- Create: `backend/app/services/challenge.py`
- Create: `backend/app/routes/challenge.py`
- Create: `backend/tests/test_challenge_service.py`

- [ ] **Step 1: Write failing test for challenge retrieval**

`backend/tests/test_challenge_service.py`:

```python
from unittest.mock import MagicMock, patch
from datetime import date
from app.services.challenge import get_todays_challenge

def test_get_todays_challenge():
    mock_supabase = MagicMock()
    today = date.today()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "date": str(today),
            "person_id": "person-1",
            "people": {
                "name": "Dwayne Johnson",
                "image_url": "https://storage.example.com/dwayne.jpg",
                "category": "actor",
                "aliases": ["The Rock"],
            },
        }
    ]
    with patch("app.services.challenge.supabase", mock_supabase):
        result = get_todays_challenge()
    assert result["image_url"] == "https://storage.example.com/dwayne.jpg"
    assert result["category"] == "actor"

def test_get_todays_challenge_no_challenge():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    with patch("app.services.challenge.supabase", mock_supabase):
        result = get_todays_challenge()
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/test_challenge_service.py -v
```

Expected: FAIL

- [ ] **Step 3: Write challenge service**

`backend/app/services/challenge.py`:

```python
from datetime import date, timezone, datetime
from app.db import supabase

def get_today_utc() -> date:
    return datetime.now(timezone.utc).date()

def get_todays_challenge() -> dict | None:
    today = get_today_utc()
    result = supabase.table("daily_challenges").select(
        "date, person_id, people(name, image_url, category, aliases)"
    ).eq("date", str(today)).execute()
    if not result.data:
        return None
    row = result.data[0]
    person = row["people"]
    return {
        "date": row["date"],
        "image_url": person["image_url"],
        "category": person["category"],
        "person_id": row["person_id"],
        "name": person["name"],
        "aliases": person["aliases"],
    }

def get_player_game_state(player_id: str, challenge_date: date) -> dict | None:
    result = supabase.table("game_results").select("*").eq(
        "player_id", player_id
    ).eq("date", str(challenge_date)).execute()
    if not result.data:
        return None
    return result.data[0]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/test_challenge_service.py -v
```

Expected: PASS

- [ ] **Step 5: Write challenge route**

`backend/app/routes/challenge.py`:

```python
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
            # Include answer if game is over
            if game_state["solved"] or game_state["guesses_used"] >= 7:
                response.answer = challenge["name"]

    return response
```

- [ ] **Step 6: Register route in main.py**

Add to `backend/app/main.py`:

```python
from app.routes.challenge import router as challenge_router
app.include_router(challenge_router)
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/challenge.py backend/app/routes/challenge.py backend/tests/test_challenge_service.py backend/app/main.py
git commit -m "feat: add daily challenge endpoint with game state resumption"
```

---

### Task 5: Guess Service + Route (Core Game Logic)

**Files:**
- Create: `backend/app/services/guess.py`
- Create: `backend/app/routes/guess.py`
- Create: `backend/tests/test_guess_service.py`

- [ ] **Step 1: Write failing tests for fuzzy matching + scoring**

`backend/tests/test_guess_service.py`:

```python
import pytest
from app.services.guess import is_correct_guess, calculate_points

def test_exact_match():
    assert is_correct_guess("Dwayne Johnson", "Dwayne Johnson", []) is True

def test_case_insensitive():
    assert is_correct_guess("dwayne johnson", "Dwayne Johnson", []) is True

def test_alias_match():
    assert is_correct_guess("The Rock", "Dwayne Johnson", ["The Rock"]) is True

def test_fuzzy_match():
    assert is_correct_guess("Dwayn Johnson", "Dwayne Johnson", []) is True

def test_wrong_guess():
    assert is_correct_guess("Brad Pitt", "Dwayne Johnson", ["The Rock"]) is False

def test_points_first_guess():
    assert calculate_points(1) == 7

def test_points_last_guess():
    assert calculate_points(7) == 1

def test_points_failed():
    assert calculate_points(0) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/test_guess_service.py -v
```

Expected: FAIL

- [ ] **Step 3: Write guess service**

`backend/app/services/guess.py`:

```python
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

    # Get challenge
    challenge = supabase.table("daily_challenges").select(
        "person_id, people(name, aliases)"
    ).eq("date", str(challenge_date)).execute()
    if not challenge.data:
        raise ValueError("No challenge for this date")

    person = challenge.data[0]["people"]
    person_name = person["name"]
    aliases = person["aliases"]

    # Check existing game state
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

    # Check guess
    correct = is_correct_guess(guess, person_name, aliases)
    guesses.append(guess)
    guesses_used += 1
    game_over = correct or guesses_used >= 7

    # Save result
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

    # Update player stats if game is over
    if game_over and correct:
        points = calculate_points(guesses_used)
        player = supabase.table("players").select("*").eq("id", player_id).execute().data[0]
        # Check if yesterday was also solved for streak
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/test_guess_service.py -v
```

Expected: PASS (the pure function tests pass; `process_guess` will be tested in integration)

- [ ] **Step 5: Write guess route**

`backend/app/routes/guess.py`:

```python
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
```

- [ ] **Step 6: Register route in main.py**

Add to `backend/app/main.py`:

```python
from app.routes.guess import router as guess_router
app.include_router(guess_router)
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/guess.py backend/app/routes/guess.py backend/tests/test_guess_service.py backend/app/main.py
git commit -m "feat: add guess endpoint with fuzzy matching, scoring, and streak tracking"
```

---

### Task 6: Leaderboard + Results Endpoints

**Files:**
- Create: `backend/app/services/leaderboard.py`
- Create: `backend/app/routes/leaderboard.py`
- Create: `backend/app/routes/results.py`
- Create: `backend/tests/test_leaderboard.py`

- [ ] **Step 1: Write failing test for leaderboard service**

`backend/tests/test_leaderboard.py`:

```python
from unittest.mock import MagicMock, patch
from datetime import date
from app.services.leaderboard import get_leaderboard

def test_get_daily_leaderboard():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"player_id": "p1", "guesses_used": 2, "players": {"nickname": "ace"}},
        {"player_id": "p2", "guesses_used": 4, "players": {"nickname": "bob"}},
    ]
    with patch("app.services.leaderboard.supabase", mock_supabase):
        result = get_leaderboard("daily")
    assert len(result["entries"]) == 2
    assert result["entries"][0]["nickname"] == "ace"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/test_leaderboard.py -v
```

- [ ] **Step 3: Write leaderboard service**

`backend/app/services/leaderboard.py`:

```python
from datetime import date, datetime, timezone, timedelta
from app.db import supabase

def get_today_utc() -> date:
    return datetime.now(timezone.utc).date()

def get_week_start(d: date) -> date:
    """Return Monday of the given date's week."""
    return d - timedelta(days=d.weekday())

def get_leaderboard(view: str, player_id: str | None = None) -> dict:
    if view == "daily":
        return _daily_leaderboard(player_id)
    elif view == "weekly":
        return _weekly_leaderboard(player_id)
    elif view == "alltime":
        return _alltime_leaderboard(player_id)
    raise ValueError(f"Invalid view: {view}")

def _daily_leaderboard(player_id: str | None) -> dict:
    today = get_today_utc()
    results = supabase.table("game_results").select(
        "player_id, guesses_used, solved, players(nickname)"
    ).eq("date", str(today)).eq("solved", True).order(
        "guesses_used", desc=False
    ).limit(50).execute()

    entries = []
    for i, row in enumerate(results.data):
        points = 8 - row["guesses_used"]
        entries.append({
            "rank": i + 1,
            "nickname": row["players"]["nickname"],
            "points": points,
            "guesses_used": row["guesses_used"],
        })

    player_rank = _find_player_rank_daily(player_id, today, entries) if player_id else None
    return {"entries": entries, "player_rank": player_rank}

def _weekly_leaderboard(player_id: str | None) -> dict:
    today = get_today_utc()
    week_start = get_week_start(today)
    week_end = week_start + timedelta(days=6)

    results = supabase.rpc("weekly_leaderboard", {
        "week_start": str(week_start),
        "week_end": str(week_end),
    }).execute()

    entries = []
    for i, row in enumerate(results.data[:50]):
        entries.append({
            "rank": i + 1,
            "nickname": row["nickname"],
            "points": row["total_points"],
        })

    player_rank = _find_player_in_entries(player_id, results.data, entries) if player_id else None
    return {"entries": entries, "player_rank": player_rank}

def _alltime_leaderboard(player_id: str | None) -> dict:
    results = supabase.table("players").select(
        "id, nickname, total_points, longest_streak"
    ).order("total_points", desc=True).limit(50).execute()

    entries = []
    for i, row in enumerate(results.data):
        entries.append({
            "rank": i + 1,
            "nickname": row["nickname"],
            "points": row["total_points"],
        })

    player_rank = None
    if player_id:
        in_top = any(e["nickname"] == row["nickname"] for e in entries for row in results.data if row["id"] == player_id)
        if not in_top:
            player_data = supabase.table("players").select(
                "nickname, total_points"
            ).eq("id", player_id).execute()
            if player_data.data:
                p = player_data.data[0]
                # Count how many players have more points
                count = supabase.table("players").select(
                    "id", count="exact"
                ).gt("total_points", p["total_points"]).execute()
                player_rank = {
                    "rank": (count.count or 0) + 1,
                    "nickname": p["nickname"],
                    "points": p["total_points"],
                }

    return {"entries": entries, "player_rank": player_rank}

def _find_player_rank_daily(player_id: str, today: date, top_entries: list) -> dict | None:
    # Check if player is already in top entries
    player_result = supabase.table("game_results").select(
        "guesses_used, players(nickname)"
    ).eq("player_id", player_id).eq("date", str(today)).eq("solved", True).execute()

    if not player_result.data:
        return None

    nickname = player_result.data[0]["players"]["nickname"]
    if any(e["nickname"] == nickname for e in top_entries):
        return None  # Already in top 50

    guesses = player_result.data[0]["guesses_used"]
    points = 8 - guesses
    count = supabase.table("game_results").select(
        "id", count="exact"
    ).eq("date", str(today)).eq("solved", True).lt("guesses_used", guesses).execute()

    return {
        "rank": (count.count or 0) + 1,
        "nickname": nickname,
        "points": points,
        "guesses_used": guesses,
    }

def _find_player_in_entries(player_id: str, all_data: list, top_entries: list) -> dict | None:
    for i, row in enumerate(all_data):
        if row.get("player_id") == player_id and i >= 50:
            return {
                "rank": i + 1,
                "nickname": row["nickname"],
                "points": row["total_points"],
            }
    return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/test_leaderboard.py -v
```

- [ ] **Step 5: Write leaderboard route**

`backend/app/routes/leaderboard.py`:

```python
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
```

- [ ] **Step 6: Write results route**

`backend/app/routes/results.py`:

```python
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
```

- [ ] **Step 7: Register routes in main.py**

Add to `backend/app/main.py`:

```python
from app.routes.leaderboard import router as leaderboard_router
from app.routes.results import router as results_router
app.include_router(leaderboard_router)
app.include_router(results_router)
```

- [ ] **Step 8: Add weekly leaderboard SQL function to schema**

Append to `database/schema.sql`:

```sql
CREATE OR REPLACE FUNCTION weekly_leaderboard(week_start DATE, week_end DATE)
RETURNS TABLE(player_id UUID, nickname TEXT, total_points BIGINT) AS $$
    SELECT
        gr.player_id,
        p.nickname,
        SUM(8 - gr.guesses_used) AS total_points
    FROM game_results gr
    JOIN players p ON p.id = gr.player_id
    WHERE gr.date BETWEEN week_start AND week_end
      AND gr.solved = true
    GROUP BY gr.player_id, p.nickname
    ORDER BY total_points DESC;
$$ LANGUAGE sql;
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/leaderboard.py backend/app/routes/leaderboard.py backend/app/routes/results.py backend/tests/test_leaderboard.py backend/app/main.py database/schema.sql
git commit -m "feat: add leaderboard (daily/weekly/alltime) and results endpoints"
```

---

## Chunk 2: Data Pipeline + Seed Scripts

### Task 7: Wikidata People Seed Script

**Files:**
- Create: `backend/scripts/seed_people.py`

- [ ] **Step 1: Write seed script**

`backend/scripts/seed_people.py`:

```python
"""Fetch famous people from Wikidata and seed the people table in Supabase.

Usage: uv run python scripts/seed_people.py --count 400
"""
import argparse
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import supabase

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

SPARQL_QUERY = """
SELECT DISTINCT ?person ?personLabel ?image ?occupation ?occupationLabel WHERE {{
  ?person wdt:P31 wd:Q5 .
  ?person wdt:P18 ?image .
  ?person wdt:P106 ?occupation .
  ?occupation wdt:P279* wd:Q2066131 .
  ?person wikibase:sitelinks ?sitelinks .
  FILTER(?sitelinks > 40)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
ORDER BY DESC(?sitelinks)
LIMIT {limit}
"""

CATEGORY_MAP = {
    "actor": ["actor", "actress", "film actor", "television actor", "voice actor"],
    "musician": ["singer", "musician", "rapper", "composer", "songwriter", "guitarist"],
    "athlete": ["athlete", "footballer", "basketball player", "tennis player", "boxer"],
    "politician": ["politician", "head of state", "president", "prime minister"],
}

def classify_category(occupation: str) -> str:
    occupation_lower = occupation.lower()
    for category, keywords in CATEGORY_MAP.items():
        if any(kw in occupation_lower for kw in keywords):
            return category
    return "other"

def fetch_people(limit: int) -> list[dict]:
    query = SPARQL_QUERY.format(limit=limit)
    resp = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": "WhoIsIt-Game/1.0"},
    )
    resp.raise_for_status()
    results = resp.json()["results"]["bindings"]

    seen = set()
    people = []
    for row in results:
        name = row["personLabel"]["value"]
        if name in seen:
            continue
        seen.add(name)
        image_url = row["image"]["value"]
        # Only use Wikimedia Commons images (permissive license)
        if "commons.wikimedia.org" not in image_url:
            continue
        category = classify_category(row.get("occupationLabel", {}).get("value", ""))
        people.append({
            "name": name,
            "aliases": [],
            "image_url": image_url,
            "category": category,
            "license": "CC-BY-SA",
            "attribution_url": image_url,
        })
    return people

def seed_database(people: list[dict]):
    # Insert in batches of 50
    for i in range(0, len(people), 50):
        batch = people[i:i+50]
        supabase.table("people").upsert(batch, on_conflict="name").execute()
        print(f"  Inserted batch {i//50 + 1} ({len(batch)} people)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=400)
    args = parser.parse_args()

    print(f"Fetching {args.count} famous people from Wikidata...")
    people = fetch_people(args.count)
    print(f"Found {len(people)} people with valid images")

    print("Seeding database...")
    seed_database(people)
    print("Done!")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/scripts/seed_people.py
git commit -m "feat: add Wikidata people seed script"
```

---

### Task 8: Challenge Generation Script

**Files:**
- Create: `backend/scripts/generate_challenges.py`

- [ ] **Step 1: Write challenge generation script**

`backend/scripts/generate_challenges.py`:

```python
"""Generate daily_challenges entries for a given year.

Usage: uv run python scripts/generate_challenges.py --year 2026
"""
import argparse
import random
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import supabase

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()

    # Fetch all people
    people = supabase.table("people").select("id").execute().data
    if not people:
        print("Error: No people in database. Run seed_people.py first.")
        return

    print(f"Found {len(people)} people in database")

    # Check for existing challenges this year
    year_start = date(args.year, 1, 1)
    year_end = date(args.year, 12, 31)
    existing = supabase.table("daily_challenges").select("date").gte(
        "date", str(year_start)
    ).lte("date", str(year_end)).execute()
    existing_dates = {row["date"] for row in existing.data}
    print(f"Found {len(existing_dates)} existing challenges for {args.year}")

    # Generate for empty dates only
    rng = random.Random(args.year)
    person_ids = [p["id"] for p in people]
    rng.shuffle(person_ids)

    # Cycle through people if we have fewer than 365
    current = year_start
    idx = 0
    new_challenges = []
    while current <= year_end:
        if str(current) not in existing_dates:
            new_challenges.append({
                "date": str(current),
                "person_id": person_ids[idx % len(person_ids)],
            })
        idx += 1
        current += timedelta(days=1)

    if not new_challenges:
        print("All dates already have challenges. Nothing to do.")
        return

    # Insert in batches
    for i in range(0, len(new_challenges), 50):
        batch = new_challenges[i:i+50]
        supabase.table("daily_challenges").insert(batch).execute()
        print(f"  Inserted batch {i//50 + 1} ({len(batch)} challenges)")

    print(f"Generated {len(new_challenges)} new challenges for {args.year}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/scripts/generate_challenges.py
git commit -m "feat: add daily challenge generation script"
```

---

## Chunk 3: Frontend Foundation

### Task 9: React Project Setup

**Files:**
- Create: `frontend/` (via Vite scaffolding)
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/styles/global.css`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`

- [ ] **Step 1: Scaffold React project with Vite**

```bash
cd whoIsIt && npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
npm install axios react-router-dom
```

- [ ] **Step 2: Create global.css with dark theme**

`frontend/src/styles/global.css`:

```css
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #2a2a4a;
  --bg-hover: #3a3a5a;
  --accent: #6c5ce7;
  --accent-hover: #7d6ff0;
  --text-primary: #ffffff;
  --text-secondary: #a0a0b8;
  --text-muted: #666680;
  --error: #e74c3c;
  --success: #2ecc71;
  --gold: #ffd700;
  --silver: #c0c0c0;
  --bronze: #cd7f32;
  --border: #4a4a7a;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: system-ui, -apple-system, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
}

button {
  cursor: pointer;
  border: none;
  font-family: inherit;
}

input {
  font-family: inherit;
}

a {
  color: var(--accent);
  text-decoration: none;
}
```

- [ ] **Step 3: Create types.ts**

`frontend/src/types.ts`:

```typescript
export interface ChallengeData {
  date: string;
  image_url: string;
  category: string | null;
  guesses_used: number | null;
  solved: boolean | null;
  guesses: string[] | null;
  answer: string | null;
}

export interface GuessResult {
  correct: boolean;
  guesses_remaining: number;
  answer?: string;
}

export interface PlayerStats {
  nickname: string;
  total_points: number;
  current_streak: number;
  longest_streak: number;
}

export interface LeaderboardEntry {
  rank: number;
  nickname: string;
  points: number;
  guesses_used?: number;
}

export interface LeaderboardData {
  entries: LeaderboardEntry[];
  player_rank: LeaderboardEntry | null;
}

export interface GameResult {
  date: string;
  guesses_used: number;
  solved: boolean;
  guesses: string[];
  points: number;
}
```

- [ ] **Step 4: Create api.ts**

`frontend/src/api.ts`:

```typescript
import axios from "axios";
import type {
  ChallengeData,
  GuessResult,
  PlayerStats,
  LeaderboardData,
} from "./types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function getChallenge(): Promise<ChallengeData> {
  const { data } = await api.get("/api/challenge/today");
  return data;
}

export async function submitGuess(
  guess: string,
  date: string
): Promise<GuessResult> {
  const { data } = await api.post("/api/guess", { guess, date });
  return data;
}

export async function createPlayer(
  nickname: string
): Promise<{ token: string; player_id: string }> {
  const { data } = await api.post("/api/player", { nickname });
  return data;
}

export async function getPlayerStats(): Promise<PlayerStats> {
  const { data } = await api.get("/api/player/me");
  return data;
}

export async function getLeaderboard(
  view: "daily" | "weekly" | "alltime"
): Promise<LeaderboardData> {
  const { data } = await api.get(`/api/leaderboard?view=${view}`);
  return data;
}
```

- [ ] **Step 5: Set up App.tsx with router**

Replace `frontend/src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import GamePage from "./pages/GamePage";
import LeaderboardPage from "./pages/LeaderboardPage";
import "./styles/global.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<GamePage />} />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 6: Create placeholder pages**

`frontend/src/pages/GamePage.tsx`:

```tsx
export default function GamePage() {
  return <div>Game Page — coming soon</div>;
}
```

`frontend/src/pages/LeaderboardPage.tsx`:

```tsx
export default function LeaderboardPage() {
  return <div>Leaderboard — coming soon</div>;
}
```

- [ ] **Step 7: Update main.tsx**

Replace `frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 8: Verify dev server starts**

```bash
cd frontend && npm run dev
# Visit http://localhost:5173 → "Game Page — coming soon"
```

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React frontend with routing, API layer, and dark theme"
```

---

### Task 10: Core Hooks (usePlayer, useGame, useCountdown)

**Files:**
- Create: `frontend/src/hooks/usePlayer.ts`
- Create: `frontend/src/hooks/useGame.ts`
- Create: `frontend/src/hooks/useCountdown.ts`

- [ ] **Step 1: Create usePlayer hook**

`frontend/src/hooks/usePlayer.ts`:

```typescript
import { useState, useEffect, useCallback } from "react";
import { createPlayer, getPlayerStats } from "../api";
import type { PlayerStats } from "../types";

export function usePlayer() {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem("token")
  );
  const [stats, setStats] = useState<PlayerStats | null>(null);
  const [loading, setLoading] = useState(false);

  const isRegistered = token !== null;

  const register = useCallback(async (nickname: string) => {
    const result = await createPlayer(nickname);
    localStorage.setItem("token", result.token);
    setToken(result.token);
  }, []);

  const refreshStats = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await getPlayerStats();
      setStats(data);
    } catch {
      // Token might be invalid
      localStorage.removeItem("token");
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) refreshStats();
  }, [token, refreshStats]);

  return { token, isRegistered, stats, register, refreshStats, loading };
}
```

- [ ] **Step 2: Create useGame hook**

`frontend/src/hooks/useGame.ts`:

```typescript
import { useState, useEffect, useCallback } from "react";
import { getChallenge, submitGuess } from "../api";
import type { ChallengeData } from "../types";

const MAX_GUESSES = 7;

export function useGame(isRegistered: boolean) {
  const [challenge, setChallenge] = useState<ChallengeData | null>(null);
  const [guesses, setGuesses] = useState<string[]>([]);
  const [guessesUsed, setGuessesUsed] = useState(0);
  const [solved, setSolved] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [guessing, setGuessing] = useState(false);

  const round = guessesUsed + 1; // Current round (1-7)

  const fetchChallenge = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getChallenge();
      setChallenge(data);
      // Restore game state if returning player
      if (data.guesses) {
        setGuesses(data.guesses);
        setGuessesUsed(data.guesses_used ?? 0);
        setSolved(data.solved ?? false);
        setGameOver(
          (data.solved ?? false) || (data.guesses_used ?? 0) >= MAX_GUESSES
        );
        if (data.answer) setAnswer(data.answer);
      }
    } catch (err) {
      console.error("Failed to load challenge:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChallenge();
  }, [fetchChallenge]);

  const makeGuess = useCallback(
    async (guess: string) => {
      if (!challenge || gameOver || guessing || !isRegistered) return;
      setGuessing(true);
      try {
        const result = await submitGuess(guess, challenge.date);
        setGuesses((prev) => [...prev, guess]);
        setGuessesUsed((prev) => prev + 1);
        if (result.correct) {
          setSolved(true);
          setGameOver(true);
          setAnswer(result.answer ?? null);
        } else if (result.guesses_remaining === 0) {
          setGameOver(true);
          setAnswer(result.answer ?? null);
        }
      } catch (err) {
        console.error("Guess failed:", err);
      } finally {
        setGuessing(false);
      }
    },
    [challenge, gameOver, guessing, isRegistered]
  );

  return {
    challenge,
    guesses,
    guessesUsed,
    solved,
    gameOver,
    answer,
    round,
    loading,
    guessing,
    makeGuess,
  };
}
```

- [ ] **Step 3: Create useCountdown hook**

`frontend/src/hooks/useCountdown.ts`:

```typescript
import { useState, useEffect } from "react";

export function useCountdown() {
  const [timeLeft, setTimeLeft] = useState("");

  useEffect(() => {
    function update() {
      const now = new Date();
      const utcMidnight = new Date(
        Date.UTC(
          now.getUTCFullYear(),
          now.getUTCMonth(),
          now.getUTCDate() + 1
        )
      );
      const diff = utcMidnight.getTime() - now.getTime();
      const hours = Math.floor(diff / 3600000);
      const minutes = Math.floor((diff % 3600000) / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeLeft(
        `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
      );
    }
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return timeLeft;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add usePlayer, useGame, and useCountdown hooks"
```

---

## Chunk 4: Frontend Components + Pages

### Task 11: Game Components

**Files:**
- Create: `frontend/src/components/PixelImage.tsx`
- Create: `frontend/src/components/GuessInput.tsx`
- Create: `frontend/src/components/GuessIndicators.tsx`
- Create: `frontend/src/components/GuessList.tsx`
- Create: `frontend/src/components/Header.tsx`
- Create: `frontend/src/components/NicknameModal.tsx`
- Create: `frontend/src/components/Countdown.tsx`

- [ ] **Step 1: Create PixelImage component**

`frontend/src/components/PixelImage.tsx`:

```tsx
import { useRef, useEffect } from "react";

const PIXEL_SIZES: Record<number, number> = {
  1: 8,
  2: 16,
  3: 24,
  4: 32,
  5: 48,
  6: 64,
  7: 128,
};

interface Props {
  src: string;
  round: number; // 1-7, or 8 for full reveal
  size?: number;
}

export default function PixelImage({ src, round, size = 260 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      canvas.width = size;
      canvas.height = size;

      if (round >= 8) {
        // Full reveal
        ctx.drawImage(img, 0, 0, size, size);
        return;
      }

      const pixelSize = PIXEL_SIZES[round] || 8;
      // Draw small
      ctx.drawImage(img, 0, 0, pixelSize, pixelSize);
      // Scale up without smoothing
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(canvas, 0, 0, pixelSize, pixelSize, 0, 0, size, size);
    };
    img.src = src;
  }, [src, round, size]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: size,
        height: size,
        borderRadius: 12,
        background: "var(--bg-secondary)",
      }}
    />
  );
}
```

- [ ] **Step 2: Create GuessInput component**

`frontend/src/components/GuessInput.tsx`:

```tsx
import { useState } from "react";

interface Props {
  onGuess: (guess: string) => void;
  disabled: boolean;
}

export default function GuessInput({ onGuess, disabled }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim() && !disabled) {
      onGuess(value.trim());
      setValue("");
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, width: "100%", maxWidth: 400 }}>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type your guess..."
        disabled={disabled}
        style={{
          flex: 1,
          padding: "10px 14px",
          borderRadius: 8,
          border: "2px solid var(--border)",
          background: "var(--bg-secondary)",
          color: "var(--text-primary)",
          fontSize: 15,
          outline: "none",
        }}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        style={{
          padding: "10px 20px",
          borderRadius: 8,
          background: disabled ? "var(--text-muted)" : "var(--accent)",
          color: "#fff",
          fontWeight: 600,
          fontSize: 15,
        }}
      >
        Guess
      </button>
    </form>
  );
}
```

- [ ] **Step 3: Create GuessIndicators component**

`frontend/src/components/GuessIndicators.tsx`:

```tsx
interface Props {
  guessesUsed: number;
  solved: boolean;
  total?: number;
}

export default function GuessIndicators({ guessesUsed, solved, total = 7 }: Props) {
  return (
    <div style={{ display: "flex", gap: 6 }}>
      {Array.from({ length: total }, (_, i) => {
        const guessNum = i + 1;
        const isUsed = guessNum <= guessesUsed;
        const isCorrect = solved && guessNum === guessesUsed;

        let bg = "var(--bg-secondary)";
        let border = "2px solid var(--border)";
        let content: string = String(guessNum);

        if (isCorrect) {
          bg = "var(--success)";
          border = "none";
          content = "\u2713";
        } else if (isUsed) {
          bg = "var(--error)";
          border = "none";
          content = "\u2717";
        }

        return (
          <div
            key={i}
            style={{
              width: 32,
              height: 32,
              borderRadius: 6,
              background: bg,
              border,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 600,
              color: isUsed ? "#fff" : "var(--text-muted)",
            }}
          >
            {content}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 4: Create GuessList component**

`frontend/src/components/GuessList.tsx`:

```tsx
interface Props {
  guesses: string[];
  solved: boolean;
}

export default function GuessList({ guesses, solved }: Props) {
  if (guesses.length === 0) return null;

  return (
    <div style={{ width: "100%", maxWidth: 400, display: "flex", flexDirection: "column", gap: 4 }}>
      {guesses.map((guess, i) => {
        const isLast = i === guesses.length - 1;
        const isCorrect = isLast && solved;
        return (
          <div
            key={i}
            style={{
              padding: "6px 12px",
              background: "var(--bg-secondary)",
              borderRadius: 6,
              fontSize: 13,
              color: isCorrect ? "var(--success)" : "var(--error)",
            }}
          >
            {i + 1}. {guess} — {isCorrect ? "\u2713" : "\u2717"}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 5: Create Header component**

`frontend/src/components/Header.tsx`:

```tsx
import { Link } from "react-router-dom";

interface Props {
  streak?: number;
}

export default function Header({ streak }: Props) {
  return (
    <header
      style={{
        width: "100%",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "16px 24px",
        maxWidth: 500,
      }}
    >
      <Link to="/" style={{ fontSize: 22, fontWeight: 700, color: "#fff", textDecoration: "none" }}>
        Who Is It?
      </Link>
      <div style={{ display: "flex", gap: 8 }}>
        {streak !== undefined && (
          <div
            style={{
              padding: "4px 10px",
              background: "var(--bg-secondary)",
              borderRadius: 6,
              fontSize: 12,
            }}
          >
            Streak: {streak}
          </div>
        )}
        <Link
          to="/leaderboard"
          style={{
            padding: "4px 10px",
            background: "var(--bg-secondary)",
            borderRadius: 6,
            fontSize: 12,
            color: "var(--text-primary)",
          }}
        >
          Leaderboard
        </Link>
      </div>
    </header>
  );
}
```

- [ ] **Step 6: Create NicknameModal component**

`frontend/src/components/NicknameModal.tsx`:

```tsx
import { useState } from "react";

interface Props {
  onRegister: (nickname: string) => Promise<void>;
}

export default function NicknameModal({ onRegister }: Props) {
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^[a-zA-Z0-9_]{3,20}$/.test(nickname)) {
      setError("3-20 characters, letters, numbers, and underscores only");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onRegister(nickname);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.8)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          background: "var(--bg-secondary)",
          padding: 32,
          borderRadius: 16,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
          maxWidth: 360,
          width: "90%",
        }}
      >
        <h2 style={{ fontSize: 24, fontWeight: 700 }}>Who Is It?</h2>
        <p style={{ color: "var(--text-secondary)", textAlign: "center", fontSize: 14 }}>
          Choose a nickname to start playing
        </p>
        <input
          value={nickname}
          onChange={(e) => setNickname(e.target.value)}
          placeholder="Enter nickname..."
          style={{
            width: "100%",
            padding: "10px 14px",
            borderRadius: 8,
            border: "2px solid var(--border)",
            background: "var(--bg-primary)",
            color: "var(--text-primary)",
            fontSize: 15,
            outline: "none",
          }}
        />
        {error && (
          <p style={{ color: "var(--error)", fontSize: 13 }}>{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: "10px",
            borderRadius: 8,
            background: "var(--accent)",
            color: "#fff",
            fontWeight: 600,
            fontSize: 15,
          }}
        >
          {loading ? "Creating..." : "Let's Play!"}
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Step 7: Create Countdown component**

`frontend/src/components/Countdown.tsx`:

```tsx
import { useCountdown } from "../hooks/useCountdown";

export default function Countdown() {
  const timeLeft = useCountdown();
  return (
    <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
      Next challenge in{" "}
      <span style={{ color: "var(--accent)", fontWeight: 600 }}>
        {timeLeft}
      </span>
    </div>
  );
}
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add all game UI components"
```

---

### Task 12: Result Screen + Share Button

**Files:**
- Create: `frontend/src/components/ResultScreen.tsx`
- Create: `frontend/src/components/ShareButton.tsx`

- [ ] **Step 1: Create ShareButton**

`frontend/src/components/ShareButton.tsx`:

```tsx
import { useState } from "react";

interface Props {
  date: string;
  guesses: string[];
  solved: boolean;
  streak: number;
}

export default function ShareButton({ date, guesses, solved, streak }: Props) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    const squares = guesses
      .map((_, i) => {
        const isLast = i === guesses.length - 1;
        if (isLast && solved) return "\uD83D\uDFE9";
        return "\uD83D\uDFE5";
      })
      .concat(Array(7 - guesses.length).fill("\u2B1C"))
      .join("");

    const guessText = solved ? `${guesses.length}/7` : "X/7";
    const text = `Who Is It? \u2014 ${date}\n${squares}\nGuessed in ${guessText} | Streak: ${streak}\nPlay at: ${window.location.origin}`;

    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleShare}
      style={{
        width: "100%",
        maxWidth: 300,
        padding: "10px",
        borderRadius: 8,
        background: "var(--accent)",
        color: "#fff",
        fontWeight: 600,
        fontSize: 14,
      }}
    >
      {copied ? "Copied!" : "Share Result"}
    </button>
  );
}
```

- [ ] **Step 2: Create ResultScreen**

`frontend/src/components/ResultScreen.tsx`:

```tsx
import PixelImage from "./PixelImage";
import GuessIndicators from "./GuessIndicators";
import ShareButton from "./ShareButton";
import Countdown from "./Countdown";
import { Link } from "react-router-dom";

interface Props {
  imageUrl: string;
  answer: string;
  solved: boolean;
  guesses: string[];
  guessesUsed: number;
  points: number;
  streak: number;
  date: string;
}

export default function ResultScreen({
  imageUrl,
  answer,
  solved,
  guesses,
  guessesUsed,
  points,
  streak,
  date,
}: Props) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 16,
        padding: 24,
      }}
    >
      <PixelImage src={imageUrl} round={8} />

      <div
        style={{
          fontSize: 22,
          fontWeight: 700,
          color: solved ? "var(--success)" : "var(--error)",
        }}
      >
        {solved ? "Correct!" : "Better luck tomorrow"}
      </div>

      <div style={{ fontSize: 18, fontWeight: 600 }}>{answer}</div>

      <GuessIndicators guessesUsed={guessesUsed} solved={solved} />

      <div style={{ display: "flex", gap: 24 }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)" }}>
            {points}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Points</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)" }}>
            {streak}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Streak</div>
        </div>
      </div>

      <ShareButton date={date} guesses={guesses} solved={solved} streak={streak} />

      <Link
        to="/leaderboard"
        style={{
          width: "100%",
          maxWidth: 300,
          padding: "10px",
          borderRadius: 8,
          background: "var(--bg-secondary)",
          color: "#fff",
          fontWeight: 600,
          fontSize: 14,
          textAlign: "center",
          border: "1px solid var(--border)",
        }}
      >
        View Leaderboard
      </Link>

      <Countdown />

      <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
        Image: <a href={imageUrl} target="_blank" rel="noopener noreferrer" style={{ color: "var(--text-muted)" }}>Attribution</a> (CC-BY-SA)
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ResultScreen.tsx frontend/src/components/ShareButton.tsx
git commit -m "feat: add result screen with share button and countdown"
```

---

### Task 13: GamePage + LeaderboardPage (Full Pages)

**Files:**
- Modify: `frontend/src/pages/GamePage.tsx`
- Modify: `frontend/src/pages/LeaderboardPage.tsx`

- [ ] **Step 1: Write GamePage**

Replace `frontend/src/pages/GamePage.tsx`:

```tsx
import { usePlayer } from "../hooks/usePlayer";
import { useGame } from "../hooks/useGame";
import Header from "../components/Header";
import PixelImage from "../components/PixelImage";
import GuessInput from "../components/GuessInput";
import GuessIndicators from "../components/GuessIndicators";
import GuessList from "../components/GuessList";
import NicknameModal from "../components/NicknameModal";
import ResultScreen from "../components/ResultScreen";

export default function GamePage() {
  const { isRegistered, stats, register, refreshStats } = usePlayer();
  const {
    challenge,
    guesses,
    guessesUsed,
    solved,
    gameOver,
    answer,
    round,
    loading,
    guessing,
    makeGuess,
  } = useGame(isRegistered);

  const handleGuess = async (guess: string) => {
    await makeGuess(guess);
    refreshStats();
  };

  if (!isRegistered) {
    return <NicknameModal onRegister={register} />;
  }

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <p style={{ color: "var(--text-muted)" }}>Loading...</p>
      </div>
    );
  }

  if (!challenge) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <p style={{ color: "var(--text-muted)" }}>No challenge available today</p>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <Header streak={stats?.current_streak} />

      {gameOver && answer ? (
        <ResultScreen
          imageUrl={challenge.image_url}
          answer={answer}
          solved={solved}
          guesses={guesses}
          guessesUsed={guessesUsed}
          points={solved ? 8 - guessesUsed : 0}
          streak={stats?.current_streak ?? 0}
          date={challenge.date}
        />
      ) : (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 16,
            padding: 24,
          }}
        >
          <PixelImage src={challenge.image_url} round={round} />

          {challenge.category && (
            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
              Hint: {challenge.category}
            </div>
          )}

          <GuessIndicators guessesUsed={guessesUsed} solved={solved} />

          <GuessInput onGuess={handleGuess} disabled={gameOver || guessing} />

          <GuessList guesses={guesses} solved={solved} />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write LeaderboardPage**

Replace `frontend/src/pages/LeaderboardPage.tsx`:

```tsx
import { useState, useEffect } from "react";
import { getLeaderboard } from "../api";
import type { LeaderboardData } from "../types";
import Header from "../components/Header";

type View = "daily" | "weekly" | "alltime";

const TABS: { label: string; value: View }[] = [
  { label: "Daily", value: "daily" },
  { label: "Weekly", value: "weekly" },
  { label: "All-Time", value: "alltime" },
];

export default function LeaderboardPage() {
  const [view, setView] = useState<View>("daily");
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getLeaderboard(view)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [view]);

  const rankColor = (rank: number) => {
    if (rank === 1) return "var(--gold)";
    if (rank === 2) return "var(--silver)";
    if (rank === 3) return "var(--bronze)";
    return "var(--text-muted)";
  };

  const rankBg = (rank: number) => {
    if (rank === 1) return "rgba(255,215,0,0.1)";
    if (rank === 2) return "rgba(192,192,192,0.08)";
    if (rank === 3) return "rgba(205,127,50,0.08)";
    return "var(--bg-secondary)";
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Header />

      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>Leaderboard</h2>

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          background: "var(--bg-secondary)",
          borderRadius: 8,
          padding: 3,
          marginBottom: 16,
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setView(tab.value)}
            style={{
              padding: "8px 20px",
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
              background: view === tab.value ? "var(--accent)" : "transparent",
              color: view === tab.value ? "#fff" : "var(--text-muted)",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading...</p>
      ) : (
        <div style={{ width: "100%", maxWidth: 460, padding: "0 16px", display: "flex", flexDirection: "column", gap: 6 }}>
          {data?.entries.map((entry) => (
            <div
              key={entry.rank}
              style={{
                display: "flex",
                alignItems: "center",
                padding: "10px 12px",
                background: rankBg(entry.rank),
                borderRadius: 8,
                border: entry.rank <= 3 ? `1px solid ${rankColor(entry.rank)}33` : "none",
              }}
            >
              <div style={{ width: 28, fontWeight: 700, color: rankColor(entry.rank), fontSize: 14 }}>
                #{entry.rank}
              </div>
              <div style={{ flex: 1, fontWeight: 600, fontSize: 14 }}>{entry.nickname}</div>
              {entry.guesses_used && (
                <div style={{ fontSize: 13, color: "var(--text-muted)", marginRight: 8 }}>
                  {entry.guesses_used} {entry.guesses_used === 1 ? "guess" : "guesses"}
                </div>
              )}
              <div style={{ fontWeight: 700, color: "var(--accent)" }}>{entry.points} pts</div>
            </div>
          ))}

          {data?.player_rank && (
            <>
              <div style={{ borderTop: "1px dashed var(--border)", margin: "6px 0" }} />
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "10px 12px",
                  background: "rgba(108,92,231,0.15)",
                  borderRadius: 8,
                  border: "1px solid rgba(108,92,231,0.3)",
                }}
              >
                <div style={{ width: 28, fontWeight: 700, color: "var(--accent)", fontSize: 14 }}>
                  #{data.player_rank.rank}
                </div>
                <div style={{ flex: 1, fontWeight: 600, fontSize: 14, color: "var(--accent)" }}>
                  {data.player_rank.nickname} (you)
                </div>
                <div style={{ fontWeight: 700, color: "var(--accent)" }}>
                  {data.player_rank.points} pts
                </div>
              </div>
            </>
          )}

          {data?.entries.length === 0 && (
            <p style={{ textAlign: "center", color: "var(--text-muted)", padding: 24 }}>
              No results yet. Be the first!
            </p>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: complete GamePage and LeaderboardPage"
```

---

## Chunk 5: Integration + Deployment

### Task 14: Supabase Setup + Run Schema

- [ ] **Step 1: Create Supabase project**

Go to https://supabase.com, create a new project. Note the URL and keys.

- [ ] **Step 2: Create `.env` files**

Create `backend/.env` from `.env.example` with real Supabase credentials.

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 3: Run schema in Supabase SQL editor**

Paste the contents of `database/schema.sql` into the Supabase SQL editor and run it.

- [ ] **Step 4: Seed people data**

```bash
cd backend && uv run python scripts/seed_people.py --count 400
```

- [ ] **Step 5: Generate challenges**

```bash
cd backend && uv run python scripts/generate_challenges.py --year 2026
```

- [ ] **Step 6: Verify end-to-end locally**

Terminal 1:
```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

Terminal 2:
```bash
cd frontend && npm run dev
```

Visit http://localhost:5173 — should see nickname prompt, then pixelated image.

- [ ] **Step 7: Commit env files**

```bash
echo ".env" >> backend/.gitignore
echo ".env" >> frontend/.gitignore
git add backend/.gitignore frontend/.gitignore backend/.env.example
git commit -m "chore: add gitignore for env files"
```

---

### Task 15: Deploy Backend to Render

- [ ] **Step 1: Create `backend/render.yaml`** (optional) or configure via Render dashboard

Add a `Procfile` or start command:

Create `backend/Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- [ ] **Step 2: Push to GitHub**

```bash
cd whoIsIt && git remote add origin https://github.com/ysugarmen/who-is-it.git
git push -u origin main
```

- [ ] **Step 3: Connect Render to repo**

In Render dashboard:
- Create new Web Service
- Connect GitHub repo, set root directory to `backend/`
- Build command: `pip install uv && uv sync`
- Start command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add environment variables from `.env`

- [ ] **Step 4: Update CORS**

Update `backend/.env` on Render to include the Vercel frontend URL in `CORS_ORIGINS`.

- [ ] **Step 5: Commit**

```bash
git add backend/Procfile
git commit -m "chore: add Procfile for Render deployment"
```

---

### Task 16: Deploy Frontend to Vercel

- [ ] **Step 1: Connect Vercel to repo**

In Vercel dashboard:
- Import GitHub repo
- Set root directory to `frontend/`
- Framework preset: Vite
- Add environment variable: `VITE_API_URL=https://your-render-app.onrender.com`

- [ ] **Step 2: Update backend CORS with Vercel URL**

Update `CORS_ORIGINS` env var on Render to include the Vercel deployment URL.

- [ ] **Step 3: Verify production**

Visit Vercel URL — full game should work end-to-end.

- [ ] **Step 4: Final commit**

```bash
git add -A && git commit -m "chore: deployment configuration complete"
```

---

## Summary

| Chunk | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-6 | Backend: project setup, DB schema, all API endpoints |
| 2 | 7-8 | Data pipeline: Wikidata seed + challenge generation |
| 3 | 9-10 | Frontend: project setup, API layer, hooks |
| 4 | 11-13 | Frontend: all components + complete pages |
| 5 | 14-16 | Integration: Supabase setup, Render + Vercel deploy |

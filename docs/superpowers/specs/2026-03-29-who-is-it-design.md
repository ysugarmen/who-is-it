# Who Is It? — Design Spec

## Overview

A daily challenge web game where players guess a famous person from a pixelated photo. Each wrong guess (up to 7) progressively de-pixelates the image. Players compete on daily, weekly, and all-time leaderboards.

## Architecture

```
┌─────────────┐       ┌──────────────┐       ┌──────────────────┐
│  React SPA  │◄─────►│   FastAPI     │◄─────►│    Supabase      │
│  (Vercel)   │       │  (Render/Fly) │       │  (DB + Storage)  │
└─────────────┘       └──────────────┘       └──────────────────┘
```

- **Frontend:** React SPA hosted on Vercel (free tier). Handles game UI, Canvas-based pixelation, result sharing, leaderboard display.
- **Backend:** FastAPI hosted on Render or Fly.io (free tier). Serves daily challenge data, validates guesses (server-side fuzzy matching), tracks scores. CORS configured to allow requests from the Vercel frontend origin.
- **Database:** Supabase PostgreSQL (free tier).
- **Image Storage:** Supabase Storage public bucket.

### Authentication Scheme
All authenticated requests use an `Authorization: Bearer <token>` header, where `<token>` is the UUID issued at player registration. This applies to both GET and POST requests.

### Timezone
All date logic uses **UTC**. Day boundaries, challenge rotation, leaderboard cutoffs, and countdown timers are all based on UTC midnight.

## Data Model

### `people`
| Column     | Type    | Description                                      |
|------------|---------|--------------------------------------------------|
| id         | UUID    | Primary key                                      |
| name       | TEXT    | Canonical name (e.g., "Dwayne Johnson")          |
| aliases    | TEXT[]  | Alternate names (e.g., ["The Rock"])              |
| image_url  | TEXT    | URL to photo in Supabase Storage                 |
| category   | TEXT    | Optional category (actor, musician, athlete, etc) |
| license    | TEXT    | Image license type (CC-BY, CC-BY-SA, public domain) |
| attribution_url | TEXT | Link to image source for attribution          |

### `daily_challenges`
| Column     | Type    | Description                         |
|------------|---------|-------------------------------------|
| id         | UUID    | Primary key                         |
| date       | DATE    | Challenge date (unique)             |
| person_id  | UUID    | FK to people                        |

**Source of truth:** The `daily_challenges` table is the canonical mapping of dates to people. A one-time seed script pre-generates entries using a seeded PRNG, but once written, the table is immutable — new people added to the pool are only assigned to future unoccupied dates.

### `players`
| Column         | Type      | Description                                    |
|----------------|-----------|------------------------------------------------|
| id             | UUID      | Primary key                                    |
| nickname       | TEXT      | Unique, 3-20 chars, alphanumeric + underscores |
| token          | UUID      | Auth token stored in localStorage              |
| current_streak | INT       | Current consecutive-day solve streak           |
| longest_streak | INT       | All-time longest streak                        |
| total_points   | INT       | Cumulative points across all games             |
| created_at     | TIMESTAMP | Registration time                              |

### `game_results`
| Column       | Type      | Description                        |
|--------------|-----------|------------------------------------|
| id           | UUID      | Primary key                        |
| player_id    | UUID      | FK to players                      |
| date         | DATE      | Challenge date                     |
| guesses_used | INT       | Number of guesses taken (1-7)      |
| solved       | BOOLEAN   | Whether they guessed correctly     |
| guesses      | TEXT[]    | Array of guesses in order          |
| completed_at | TIMESTAMP | When the game was finished         |

Unique constraint on (player_id, date) — one attempt per day.

## Game Mechanics

### Pixelation Levels
7 rounds of play, each with decreasing pixelation. Controlled client-side via Canvas API:
- Round 1 (first view): ~8x8 pixel blocks — heavily pixelated
- Round 2: ~16x16
- Round 3: ~24x24
- Round 4: ~32x32
- Round 5: ~48x48
- Round 6: ~64x64
- Round 7 (final guess): ~128x128 — nearly clear

Technique: downscale image to target resolution, then upscale back with `imageSmoothingEnabled = false`.

After all 7 guesses or a correct guess: reveal the full original image.

### Guess Validation
- Free text input on the client
- **Server-side fuzzy matching** using `thefuzz` (Python) against the person's name + aliases
- Case insensitive, accent insensitive
- Configurable similarity threshold (e.g., 85% match ratio)
- The answer is never sent to the client until the game is over (correct guess or all 7 used)

### Scoring
- `8 - guesses_used` points for a correct answer (first try = 7 pts, last try = 1 pt)
- 0 points for failure
- Streak: consecutive days (UTC) with a correct guess
- Any day without a solved `game_results` row breaks the streak (covers both skipped days and failed attempts)

### Daily Flow
1. Player opens site → sees heavily pixelated image (round 1)
2. Types guess → sent to backend → backend returns correct/incorrect
3. Wrong: frontend de-pixelates one level, shows "X guesses remaining"
4. Correct: celebration animation, backend returns person name, reveal full image, show stats
5. All 7 wrong: backend returns person name, reveal answer, show "better luck tomorrow"
6. Once completed (win or lose): locked for the day, show results + leaderboard
7. Countdown timer to next UTC midnight

## Player System

### Nickname Auth
- First visit: prompt for nickname (3-20 chars, alphanumeric + underscores)
- Backend generates UUID token, stored in localStorage
- Token sent via `Authorization: Bearer <token>` header
- Nickname uniqueness enforced
- Lost token = new nickname required

### Anti-Gaming
- Rate limit: 7 guesses per token per day (primary), plus 50 guesses per IP per day (to limit abuse from mass-created accounts)
- Account creation rate limit: 5 new accounts per IP per day
- Nickname uniqueness
- No replay of past days for points

## Leaderboard

### Views
- **Daily:** Today's results — who solved it, in how many guesses
- **Weekly:** Total points accumulated this week (Monday–Sunday UTC)
- **All-Time:** Cumulative total points + longest streak

### Display
- Top 50 entries per view
- Player's own rank highlighted, shown at bottom if outside top 50
- Gold/silver/bronze styling for top 3

## API Endpoints

All authenticated endpoints require `Authorization: Bearer <token>` header.

### `GET /api/challenge/today`
Returns today's challenge: `{ date, image_url, category }`. Does NOT return the answer. If the player has already played today (token provided), also returns their game state: `{ guesses_used, solved, guesses: string[] }` so the UI can restore previous guesses and the correct pixelation level on page refresh.

### `POST /api/guess`
Body: `{ guess, date }` — validates guess server-side, returns `{ correct: bool, guesses_remaining: int, answer?: string }`. The `answer` field is only included when the game is over (correct guess or 0 remaining). The `date` field prevents midnight-boundary ambiguity.

### `GET /api/player/me`
Returns the authenticated player's stats: `{ nickname, total_points, current_streak, longest_streak, rank }`.

### `GET /api/results/{date}`
Returns the authenticated player's results for a given date.

### `GET /api/leaderboard?view=daily|weekly|alltime`
Returns leaderboard data: `{ entries: [{ rank, nickname, points, guesses_used? }], player_rank?: { rank, nickname, points } }`. The `player_rank` field is included when the player is authenticated and outside the top 50.

### `POST /api/player`
Body: `{ nickname }` — creates player, returns `{ token, player_id }`.

### Error Responses
All endpoints return standard HTTP status codes:
- `400` — invalid input (bad nickname format, empty guess, invalid date)
- `401` — missing or invalid token
- `404` — resource not found
- `409` — conflict (duplicate nickname, already played today)
- `429` — rate limit exceeded
- `500` — server error

Error body: `{ detail: string }`.

## UI Design

### Theme
Dark theme (#1a1a2e background, #6c5ce7 accent purple).

### Game Screen
- Header: logo, streak counter, leaderboard link
- Center: pixelated image (260x260)
- Below image: 7 guess indicator slots (red X for wrong, green check for correct, dim for unused)
- Text input + "Guess" button
- Previous wrong guesses listed below input

### Win/Lose Screen
- Revealed full image
- "Correct!" / "Better luck tomorrow" message
- Person's name
- Guess indicators
- Stats: points, streak, rank
- "Share Result" and "View Leaderboard" buttons
- Countdown to next challenge (UTC midnight)

### Share Result
Copies a text block to clipboard (via Clipboard API) in this format:
```
Who Is It? — 2026-03-29
🟥🟥🟩⬜⬜⬜⬜
Guessed in 3/7 | Streak: 6
Play at: [URL]
```
Emoji squares represent guesses: red = wrong, green = correct, gray = unused. "3/7" means solved on guess 3 of 7. No spoilers.

### Leaderboard Screen
- Tab bar: Daily / Weekly / All-Time
- Ranked list with rank, nickname, guess count, points
- Top 3 with gold/silver/bronze accent
- Player's own rank highlighted at bottom

## Image Pool

### Source
Automated via Wikipedia/Wikidata. Build a script to:
1. Fetch a list of well-known people from Wikidata (actors, musicians, athletes, politicians, etc.)
2. Download their primary Wikipedia image
3. Filter for quality (face clearly visible, good resolution)
4. Upload to Supabase Storage
5. Insert into `people` table with name + aliases

**Licensing:** Only use images with permissive licenses (CC-BY, CC-BY-SA, public domain). Store the license type per image. Include attribution link in the reveal screen.

Target: 365+ entries for a full year of daily challenges without repeats.

### Challenge Generation
One-time seed script generates `daily_challenges` entries:
- Seed = year, shuffle the people pool, assign one per day
- Once written, entries are immutable
- New people added to the pool are assigned to future empty dates only
- Existing date→person mappings never change

## Tech Stack

| Layer      | Technology          | Hosting         |
|------------|---------------------|-----------------|
| Frontend   | React + Vite        | Vercel (free)   |
| Backend    | FastAPI + Python     | Render (free)   |
| Database   | PostgreSQL           | Supabase (free) |
| Storage    | Supabase Storage     | Supabase (free) |
| Fuzzy Match | thefuzz (server)   | —               |
| Pixelation | Canvas API (client)  | —               |

## Known Tradeoffs

These are deliberate choices accepted for a casual, low-stakes game:

- **UUID token auth has no expiration or revocation.** Acceptable since there are no sensitive user data or real accounts — worst case is someone impersonates a nickname.
- **Original image URL is exposed to the client.** A technically savvy player could fetch it directly from Supabase Storage. Acceptable for a casual game; if it becomes a problem, images can be proxied through the backend later.
- **`guesses_used` is derivable from `guesses` array length.** Intentional denormalization for simpler queries. `guesses` array is the source of truth.
- **No API versioning.** Out of scope for v1. Can be added later if needed.

## Dependencies

### Frontend
- react, react-dom
- axios (API calls)
- react-router-dom (routing)

### Backend
- fastapi, uvicorn
- supabase-py (Supabase client)
- thefuzz (fuzzy string matching)
- python-dotenv
- pydantic

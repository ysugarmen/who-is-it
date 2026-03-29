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

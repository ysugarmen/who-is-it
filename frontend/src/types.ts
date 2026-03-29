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

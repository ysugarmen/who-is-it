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

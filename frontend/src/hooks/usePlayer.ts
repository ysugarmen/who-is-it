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

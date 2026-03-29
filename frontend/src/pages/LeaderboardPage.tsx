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

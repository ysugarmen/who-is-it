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

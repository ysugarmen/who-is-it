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

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

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

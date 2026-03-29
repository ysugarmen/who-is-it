interface Props {
  guessesUsed: number;
  solved: boolean;
  total?: number;
}

export default function GuessIndicators({ guessesUsed, solved, total = 7 }: Props) {
  return (
    <div style={{ display: "flex", gap: 6 }}>
      {Array.from({ length: total }, (_, i) => {
        const guessNum = i + 1;
        const isUsed = guessNum <= guessesUsed;
        const isCorrect = solved && guessNum === guessesUsed;

        let bg = "var(--bg-secondary)";
        let border = "2px solid var(--border)";
        let content: string = String(guessNum);

        if (isCorrect) {
          bg = "var(--success)";
          border = "none";
          content = "\u2713";
        } else if (isUsed) {
          bg = "var(--error)";
          border = "none";
          content = "\u2717";
        }

        return (
          <div
            key={i}
            style={{
              width: 32,
              height: 32,
              borderRadius: 6,
              background: bg,
              border,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 600,
              color: isUsed ? "#fff" : "var(--text-muted)",
            }}
          >
            {content}
          </div>
        );
      })}
    </div>
  );
}

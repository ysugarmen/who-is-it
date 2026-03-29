import { useState } from "react";

interface Props {
  onGuess: (guess: string) => void;
  disabled: boolean;
}

export default function GuessInput({ onGuess, disabled }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim() && !disabled) {
      onGuess(value.trim());
      setValue("");
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, width: "100%", maxWidth: 400 }}>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Type your guess..."
        disabled={disabled}
        style={{
          flex: 1,
          padding: "10px 14px",
          borderRadius: 8,
          border: "2px solid var(--border)",
          background: "var(--bg-secondary)",
          color: "var(--text-primary)",
          fontSize: 15,
          outline: "none",
        }}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        style={{
          padding: "10px 20px",
          borderRadius: 8,
          background: disabled ? "var(--text-muted)" : "var(--accent)",
          color: "#fff",
          fontWeight: 600,
          fontSize: 15,
        }}
      >
        Guess
      </button>
    </form>
  );
}

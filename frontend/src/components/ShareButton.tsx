import { useState } from "react";

interface Props {
  date: string;
  guesses: string[];
  solved: boolean;
  streak: number;
}

export default function ShareButton({ date, guesses, solved, streak }: Props) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    const squares = guesses
      .map((_, i) => {
        const isLast = i === guesses.length - 1;
        if (isLast && solved) return "\uD83D\uDFE9";
        return "\uD83D\uDFE5";
      })
      .concat(Array(7 - guesses.length).fill("\u2B1C"))
      .join("");

    const guessText = solved ? `${guesses.length}/7` : "X/7";
    const text = `Who Is It? \u2014 ${date}\n${squares}\nGuessed in ${guessText} | Streak: ${streak}\nPlay at: ${window.location.origin}`;

    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleShare}
      style={{
        width: "100%",
        maxWidth: 300,
        padding: "10px",
        borderRadius: 8,
        background: "var(--accent)",
        color: "#fff",
        fontWeight: 600,
        fontSize: 14,
      }}
    >
      {copied ? "Copied!" : "Share Result"}
    </button>
  );
}

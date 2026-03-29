import { usePlayer } from "../hooks/usePlayer";
import { useGame } from "../hooks/useGame";
import Header from "../components/Header";
import PixelImage from "../components/PixelImage";
import GuessInput from "../components/GuessInput";
import GuessIndicators from "../components/GuessIndicators";
import GuessList from "../components/GuessList";
import NicknameModal from "../components/NicknameModal";
import ResultScreen from "../components/ResultScreen";

export default function GamePage() {
  const { isRegistered, stats, register, refreshStats } = usePlayer();
  const {
    challenge,
    guesses,
    guessesUsed,
    solved,
    gameOver,
    answer,
    round,
    loading,
    guessing,
    makeGuess,
  } = useGame(isRegistered);

  const handleGuess = async (guess: string) => {
    await makeGuess(guess);
    refreshStats();
  };

  if (!isRegistered) {
    return <NicknameModal onRegister={register} />;
  }

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <p style={{ color: "var(--text-muted)" }}>Loading...</p>
      </div>
    );
  }

  if (!challenge) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <p style={{ color: "var(--text-muted)" }}>No challenge available today</p>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <Header streak={stats?.current_streak} />

      {gameOver && answer ? (
        <ResultScreen
          imageUrl={challenge.image_url}
          answer={answer}
          solved={solved}
          guesses={guesses}
          guessesUsed={guessesUsed}
          points={solved ? 8 - guessesUsed : 0}
          streak={stats?.current_streak ?? 0}
          date={challenge.date}
        />
      ) : (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 16,
            padding: 24,
          }}
        >
          <PixelImage src={challenge.image_url} round={round} />

          {challenge.category && (
            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
              Hint: {challenge.category}
            </div>
          )}

          <GuessIndicators guessesUsed={guessesUsed} solved={solved} />

          <GuessInput onGuess={handleGuess} disabled={gameOver || guessing} />

          <GuessList guesses={guesses} solved={solved} />
        </div>
      )}
    </div>
  );
}

import { useState, useEffect, useCallback } from "react";
import { getChallenge, submitGuess } from "../api";
import type { ChallengeData } from "../types";

const MAX_GUESSES = 7;

export function useGame(isRegistered: boolean) {
  const [challenge, setChallenge] = useState<ChallengeData | null>(null);
  const [guesses, setGuesses] = useState<string[]>([]);
  const [guessesUsed, setGuessesUsed] = useState(0);
  const [solved, setSolved] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [guessing, setGuessing] = useState(false);

  const round = guessesUsed + 1;

  const fetchChallenge = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getChallenge();
      setChallenge(data);
      if (data.guesses) {
        setGuesses(data.guesses);
        setGuessesUsed(data.guesses_used ?? 0);
        setSolved(data.solved ?? false);
        setGameOver(
          (data.solved ?? false) || (data.guesses_used ?? 0) >= MAX_GUESSES
        );
        if (data.answer) setAnswer(data.answer);
      }
    } catch (err) {
      console.error("Failed to load challenge:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChallenge();
  }, [fetchChallenge]);

  const makeGuess = useCallback(
    async (guess: string) => {
      if (!challenge || gameOver || guessing || !isRegistered) return;
      setGuessing(true);
      try {
        const result = await submitGuess(guess, challenge.date);
        setGuesses((prev) => [...prev, guess]);
        setGuessesUsed((prev) => prev + 1);
        if (result.correct) {
          setSolved(true);
          setGameOver(true);
          setAnswer(result.answer ?? null);
        } else if (result.guesses_remaining === 0) {
          setGameOver(true);
          setAnswer(result.answer ?? null);
        }
      } catch (err) {
        console.error("Guess failed:", err);
      } finally {
        setGuessing(false);
      }
    },
    [challenge, gameOver, guessing, isRegistered]
  );

  return {
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
  };
}

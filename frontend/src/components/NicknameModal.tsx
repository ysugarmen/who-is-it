import { useState } from "react";

interface Props {
  onRegister: (nickname: string) => Promise<void>;
}

export default function NicknameModal({ onRegister }: Props) {
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^[a-zA-Z0-9_]{3,20}$/.test(nickname)) {
      setError("3-20 characters, letters, numbers, and underscores only");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onRegister(nickname);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.8)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          background: "var(--bg-secondary)",
          padding: 32,
          borderRadius: 16,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
          maxWidth: 360,
          width: "90%",
        }}
      >
        <h2 style={{ fontSize: 24, fontWeight: 700 }}>Who Is It?</h2>
        <p style={{ color: "var(--text-secondary)", textAlign: "center", fontSize: 14 }}>
          Choose a nickname to start playing
        </p>
        <input
          value={nickname}
          onChange={(e) => setNickname(e.target.value)}
          placeholder="Enter nickname..."
          style={{
            width: "100%",
            padding: "10px 14px",
            borderRadius: 8,
            border: "2px solid var(--border)",
            background: "var(--bg-primary)",
            color: "var(--text-primary)",
            fontSize: 15,
            outline: "none",
          }}
        />
        {error && (
          <p style={{ color: "var(--error)", fontSize: 13 }}>{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: "10px",
            borderRadius: 8,
            background: "var(--accent)",
            color: "#fff",
            fontWeight: 600,
            fontSize: 15,
          }}
        >
          {loading ? "Creating..." : "Let's Play!"}
        </button>
      </form>
    </div>
  );
}

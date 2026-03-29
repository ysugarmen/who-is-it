import { useRef, useEffect } from "react";

const PIXEL_SIZES: Record<number, number> = {
  1: 8,
  2: 16,
  3: 24,
  4: 32,
  5: 48,
  6: 64,
  7: 128,
};

interface Props {
  src: string;
  round: number;
  size?: number;
}

export default function PixelImage({ src, round, size = 260 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onerror = () => {
      // Fallback: try without crossOrigin (won't pixelate but will show image)
      const fallback = new Image();
      fallback.onload = () => {
        canvas.width = size;
        canvas.height = size;
        ctx.drawImage(fallback, 0, 0, size, size);
      };
      fallback.src = src;
    };
    img.onload = () => {
      canvas.width = size;
      canvas.height = size;

      if (round >= 8) {
        ctx.drawImage(img, 0, 0, size, size);
        return;
      }

      const pixelSize = PIXEL_SIZES[round] || 8;
      ctx.drawImage(img, 0, 0, pixelSize, pixelSize);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(canvas, 0, 0, pixelSize, pixelSize, 0, 0, size, size);
    };
    // Proxy through backend to avoid CORS issues with Wikimedia
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    img.src = `${apiUrl}/api/image-proxy?url=${encodeURIComponent(src)}`;
  }, [src, round, size]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: size,
        height: size,
        borderRadius: 12,
        background: "var(--bg-secondary)",
      }}
    />
  );
}

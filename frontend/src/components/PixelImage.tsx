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
    img.onload = () => {
      canvas.width = size;
      canvas.height = size;

      if (round >= 8) {
        ctx.drawImage(img, 0, 0, size, size);
        return;
      }

      const pixelSize = PIXEL_SIZES[round] || 8;

      // Use offscreen canvas for clean pixelation
      const offscreen = document.createElement("canvas");
      offscreen.width = pixelSize;
      offscreen.height = pixelSize;
      const offCtx = offscreen.getContext("2d")!;

      // Draw image at tiny size
      offCtx.drawImage(img, 0, 0, pixelSize, pixelSize);

      // Scale up to full size without smoothing
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(offscreen, 0, 0, pixelSize, pixelSize, 0, 0, size, size);
    };
    img.onerror = () => {
      // Fallback: proxy through backend
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const proxyImg = new Image();
      proxyImg.crossOrigin = "anonymous";
      proxyImg.onload = () => {
        canvas.width = size;
        canvas.height = size;

        if (round >= 8) {
          ctx.drawImage(proxyImg, 0, 0, size, size);
          return;
        }

        const pixelSize = PIXEL_SIZES[round] || 8;
        const offscreen = document.createElement("canvas");
        offscreen.width = pixelSize;
        offscreen.height = pixelSize;
        const offCtx = offscreen.getContext("2d")!;
        offCtx.drawImage(proxyImg, 0, 0, pixelSize, pixelSize);
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(offscreen, 0, 0, pixelSize, pixelSize, 0, 0, size, size);
      };
      proxyImg.src = `${apiUrl}/api/image-proxy?url=${encodeURIComponent(src)}`;
    };
    // Try direct URL first (upload.wikimedia.org has CORS support)
    img.src = src;
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

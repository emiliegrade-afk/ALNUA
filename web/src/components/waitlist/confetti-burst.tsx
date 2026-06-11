"use client";

import { useEffect, useState } from "react";

interface ConfettiBurstProps {
  active: boolean;
}

/** Lightweight CSS confetti — no extra dependency. */
export function ConfettiBurst({ active }: ConfettiBurstProps) {
  const [pieces, setPieces] = useState<
    { id: number; left: number; delay: number; color: string; size: number }[]
  >([]);

  useEffect(() => {
    if (!active) {
      setPieces([]);
      return;
    }

    const colors = ["#C08A72", "#F5E6D3", "#22c55e", "#f59e0b", "#ec4899"];
    setPieces(
      Array.from({ length: 48 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 0.6,
        color: colors[i % colors.length] ?? colors[0],
        size: 6 + Math.random() * 6,
      }))
    );

    const timer = setTimeout(() => setPieces([]), 3200);
    return () => clearTimeout(timer);
  }, [active]);

  if (pieces.length === 0) return null;

  return (
    <div
      className="pointer-events-none fixed inset-0 z-50 overflow-hidden"
      aria-hidden
    >
      {pieces.map((p) => (
        <span
          key={p.id}
          className="absolute top-0 animate-confetti-fall rounded-sm opacity-90"
          style={{
            left: `${p.left}%`,
            width: p.size,
            height: p.size * 0.6,
            backgroundColor: p.color,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}

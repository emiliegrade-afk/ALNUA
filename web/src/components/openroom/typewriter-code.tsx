"use client";

import { useEffect, useState } from "react";

export function TypewriterCode({ lines }: { lines: string[] }) {
  const [displayed, setDisplayed] = useState<string[]>([]);
  const [currentLine, setCurrentLine] = useState(0);
  const [currentChar, setCurrentChar] = useState(0);

  useEffect(() => {
    setDisplayed([]);
    setCurrentLine(0);
    setCurrentChar(0);
  }, [lines]);

  useEffect(() => {
    if (currentLine >= lines.length) return;
    if (currentChar >= lines[currentLine].length) {
      const t = setTimeout(() => {
        setDisplayed((prev) => [...prev, lines[currentLine]]);
        setCurrentLine((l) => l + 1);
        setCurrentChar(0);
      }, 200);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setCurrentChar((c) => c + 1), 35);
    return () => clearTimeout(t);
  }, [currentLine, currentChar, lines]);

  return (
    <div className="space-y-0.5">
      {displayed.map((line, i) => (
        <div key={i} className="text-copper/70">
          {line}
        </div>
      ))}
      {currentLine < lines.length ? (
        <div className="text-copper/70">
          {lines[currentLine].slice(0, currentChar)}
          <span className="animate-pulse">▋</span>
        </div>
      ) : null}
    </div>
  );
}

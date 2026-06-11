"use client";

import { useEffect, useState } from "react";

/** Affichage progressif mot par mot (simulation streaming côté client). */
export function useStreamingText(fullText: string, active: boolean, speedMs = 18) {
  const [displayed, setDisplayed] = useState(active ? "" : fullText);

  useEffect(() => {
    if (!active) {
      setDisplayed(fullText);
      return;
    }

    setDisplayed("");
    const words = fullText.split(/(\s+)/);
    let index = 0;

    const timer = setInterval(() => {
      index += 1;
      setDisplayed(words.slice(0, index).join(""));
      if (index >= words.length) {
        clearInterval(timer);
      }
    }, speedMs);

    return () => clearInterval(timer);
  }, [fullText, active, speedMs]);

  const isStreaming = active && displayed.length < fullText.length;
  return { displayed, isStreaming };
}

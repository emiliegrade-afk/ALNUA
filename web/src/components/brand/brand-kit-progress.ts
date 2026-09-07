import { ALL_FORMAT_NAMES } from "@/lib/brand-api";

/** Fake progress while kit formats generate (client-side UX only). */
export function startKitProgress(
  timerRef: { current: ReturnType<typeof setInterval> | null },
  setProgress: (n: number) => void,
  setLabel: (s: string) => void,
) {
  let index = 0;
  setProgress(0);
  setLabel(ALL_FORMAT_NAMES[0] ?? "");
  timerRef.current = setInterval(() => {
    index = Math.min(index + 1, ALL_FORMAT_NAMES.length - 1);
    setLabel(ALL_FORMAT_NAMES[index] ?? "");
    setProgress(Math.round(((index + 1) / ALL_FORMAT_NAMES.length) * 92));
  }, 800);
}

export function stopKitProgress(
  timerRef: { current: ReturnType<typeof setInterval> | null },
  setProgress: (n: number) => void,
  finalProgress = 100,
) {
  if (timerRef.current) {
    clearInterval(timerRef.current);
    timerRef.current = null;
  }
  setProgress(finalProgress);
}

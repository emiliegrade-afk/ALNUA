/** « Tout effacer » — screens only, never the task list (SPEC_JARVIS_LIVE §14). */

const CLEAR_RE =
  /\b(tout\s+effacer|efface(?:r)?(?:\s+(?:tout|les?\s+écrans?|l['’]écran))?|clear\s+(?:all|screens?)|vide(?:r)?\s+l['’]écran)\b/i;

export function wantsClearScreens(text: string): boolean {
  return CLEAR_RE.test((text || "").trim());
}

/** Pull a real OAuth URL out of mixed Hub replies (Gmail wraps the link in a hint). */

export function extractOAuthUrl(text: string): string | null {
  const match = text.match(/https?:\/\/[^\s)\]>'"<>]+/);
  if (!match) return null;
  return match[0].replace(/[.,;]+$/, "");
}

/**
 * Open the popup in the click handler (empty tab), then point it at the URL.
 * `window.open` after `await` is blocked by the browser — that is why Connecter
 * Gmail looked like it did nothing.
 */
export function fillOAuthPopup(popup: Window | null, url: string): boolean {
  if (popup && !popup.closed) {
    popup.location.replace(url);
    return true;
  }
  return false;
}

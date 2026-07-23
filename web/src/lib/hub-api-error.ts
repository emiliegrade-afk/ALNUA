/** Extract a human-readable message from Hub API error bodies. */
export function parseHubApiError(text: string, status: number): string {
  const trimmed = text.trim();
  if (!trimmed) {
    return `Erreur API (${status})`;
  }

  try {
    const json = JSON.parse(trimmed) as { detail?: unknown };
    const detail = json.detail;
    if (typeof detail === "string" && detail.length > 0) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
  } catch {
    // not JSON — fall through
  }

  if (status === 404 && trimmed.toLowerCase().includes("not found")) {
    return "Route API introuvable — redémarre le backend (uvicorn --reload port 8000) pour charger les dernières routes.";
  }
  if (status === 502) {
    return "Backend Hub inaccessible — lance Demarrer-Hub.bat.";
  }
  if (status === 500) {
    return "Le serveur Hub est surcharge ou en erreur — attends 30 s puis recharge la page.";
  }
  if (status === 503 && trimmed.includes("HUB_API_KEY")) {
    return "Clé API manquante — configure HUB_API_KEY dans web/.env.local.";
  }

  return trimmed.length > 200 ? `Erreur API (${status})` : trimmed;
}

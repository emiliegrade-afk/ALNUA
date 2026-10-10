/** Parse chart / summary blocks from agent text. Never treat the text as HTML. */

export interface ChartPoint {
  label: string;
  value: number;
}

export interface ChartSeries {
  title: string;
  points: ChartPoint[];
}

export interface SummaryBrief {
  headline: string;
  bullets: string[];
}

const FENCE = /```(?:chart|summary|json)\s*([\s\S]*?)```/i;
const ROW = /^(.+?)\s*[:|—–-]\s*(-?\d+(?:[.,]\d+)?)\s*$/;

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function pointsFrom(raw: unknown): ChartPoint[] {
  if (!Array.isArray(raw)) return [];
  const points: ChartPoint[] = [];
  for (const item of raw) {
    const row = asRecord(item);
    if (!row) continue;
    const label = String(row.label ?? "").trim();
    const value = Number(row.value);
    if (!label || !Number.isFinite(value)) continue;
    points.push({ label: label.slice(0, 40), value });
  }
  return points.slice(0, 12);
}

function parseJsonObject(text: string): Record<string, unknown> | null {
  try {
    return asRecord(JSON.parse(text));
  } catch {
    return null;
  }
}

export function parseChart(text: string): ChartSeries | null {
  const fence = FENCE.exec(text);
  const candidate = fence ? fence[1].trim() : text.trim();
  const obj = parseJsonObject(candidate);
  if (obj) {
    const points = pointsFrom(obj.points);
    if (points.length >= 2) {
      return { title: String(obj.title ?? "Graphique"), points };
    }
  }
  const rows: ChartPoint[] = [];
  for (const line of text.split("\n")) {
    const m = ROW.exec(line.trim());
    if (!m) continue;
    rows.push({ label: m[1].trim().slice(0, 40), value: Number(m[2].replace(",", ".")) });
  }
  if (rows.length < 3) return null;
  return { title: "Graphique", points: rows.slice(0, 12) };
}

export interface ListBrief {
  title: string;
  items: string[];
}

export interface ImageBrief {
  title: string;
  src: string;
  credit: string;
  href: string;
}

export interface DraftBrief {
  kind: "linkedin" | "email" | "pc_input";
  title: string;
  body: string;
  draftId: string;
}

function fenceOf(kind: string, text: string): string | null {
  const fence = new RegExp("```" + kind + "\\s*([\\s\\S]*?)```", "i").exec(text);
  return fence ? fence[1].trim() : null;
}

export function parseList(text: string): ListBrief | null {
  const raw = fenceOf("list", text);
  if (!raw) return null;
  const obj = parseJsonObject(raw);
  if (!obj) return null;
  const title = String(obj.title ?? "").trim();
  const items = Array.isArray(obj.items)
    ? obj.items.map((item) => String(item).trim()).filter(Boolean).slice(0, 12)
    : [];
  if (!title || items.length < 1) return null;
  return { title: title.slice(0, 120), items };
}

export function parseImage(text: string): ImageBrief | null {
  const raw = fenceOf("image", text);
  if (!raw) return null;
  const obj = parseJsonObject(raw);
  if (!obj) return null;
  const src = String(obj.src ?? "").trim();
  const title = String(obj.title ?? "Image").trim() || "Image";
  if (!src) return null;
  return {
    title: title.slice(0, 120),
    src: src.slice(0, 400),
    credit: String(obj.credit ?? "").trim().slice(0, 200),
    href: String(obj.href ?? "").trim().slice(0, 400),
  };
}

export function parseDraft(text: string): DraftBrief | null {
  const raw = fenceOf("draft", text);
  if (!raw) return null;
  const obj = parseJsonObject(raw);
  if (!obj) return null;
  const kind = String(obj.kind ?? "").trim();
  const draftId = String(obj.draft_id ?? "").trim();
  const body = String(obj.body ?? "").trim();
  if ((kind !== "linkedin" && kind !== "email" && kind !== "pc_input") || !draftId || !body) {
    return null;
  }
  return {
    kind,
    title: String(obj.title ?? "Brouillon").trim().slice(0, 160) || "Brouillon",
    body: body.slice(0, 4000),
    draftId: draftId.slice(0, 64),
  };
}

/** Only Hub-generated PNGs and Wikimedia HTTPS — never a random agent URL. */
export function safeImageSrc(src: string): string | null {
  if (/^\/api\/hub\/live\/media\/[a-f0-9]{32}\.png$/.test(src)) return src;
  try {
    const url = new URL(src);
    if (url.protocol !== "https:") return null;
    const host = url.hostname.toLowerCase();
    if (host === "upload.wikimedia.org" || host.endsWith(".wikimedia.org")) return src;
    return null;
  } catch {
    return null;
  }
}

export function parseSummary(text: string): SummaryBrief | null {
  const fence = /```summary\s*([\s\S]*?)```/i.exec(text);
  if (fence) {
    const obj = parseJsonObject(fence[1].trim());
    if (obj) {
      const headline = String(obj.headline ?? "").trim();
      const bullets = Array.isArray(obj.bullets)
        ? obj.bullets.map((b) => String(b).trim()).filter(Boolean).slice(0, 8)
        : [];
      if (headline && bullets.length) return { headline, bullets };
    }
  }
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  if (lines.length < 3) return null;
  const bullets = lines
    .slice(1)
    .filter((l) => /^[-*•]/.test(l))
    .map((l) => l.replace(/^[-*•]\s*/, "").trim())
    .filter(Boolean);
  if (bullets.length < 2) return null;
  return { headline: lines[0].slice(0, 160), bullets: bullets.slice(0, 8) };
}

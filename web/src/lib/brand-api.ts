import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";
import { hubFetch } from "./hub-fetch";

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface BrandElement {
  label: string;
  type: string;
  bbox: BoundingBox;
  description: string;
}

export interface ColorInfo {
  hex: string;
  name: string;
  role: string;
  source: "llm" | "kmeans" | "merged";
}

export interface BrandAnalysis {
  brand_name: string;
  tagline: string | null;
  style: string;
  mood: string[];
  typography_style: string;
  colors: ColorInfo[];
  elements: BrandElement[];
  usage_notes: string;
  components: Record<string, boolean>;
  upload_path?: string;
  segment_paths?: Record<string, string>;
  isolated_assets?: Record<string, string>;
  generated_assets?: Record<string, string>;
  report_path?: string;
}

export interface BrandAnalyzeResult {
  kit_id?: string | null;
  analysis: BrandAnalysis;
  upload_path: string;
  segment_paths?: Record<string, string>;
  isolated_assets?: Record<string, string>;
}

export interface BrandKitSummary {
  id: string;
  project_id: string;
  brand_name: string;
  assets_path: string;
  formats_generated: string[];
  is_complete: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface BrandKitDetail extends BrandKitSummary {
  analysis: BrandAnalysis;
  generated_assets: Record<string, string>;
  report_path?: string | null;
  upload_path?: string | null;
  segment_paths: Record<string, string>;
  isolated_assets: Record<string, string>;
}

export interface BrandGenerateKitResult {
  kit_id?: string;
  assets: Record<string, string>;
  report_path: string;
  zip_url: string;
  formats_generated: string[];
}

export const FORMAT_CATEGORIES: Record<
  string,
  { label: string; formats: string[] }
> = {
  profiles: {
    label: "Profils",
    formats: [
      "instagram_profile",
      "tiktok_profile",
      "x_profile",
      "youtube_profile",
      "linkedin_profile",
      "favicon",
      "app_icon",
    ],
  },
  banners: {
    label: "Bannières",
    formats: [
      "x_header",
      "youtube_banner",
      "linkedin_banner",
      "facebook_cover",
    ],
  },
  posts: {
    label: "Posts & Stories",
    formats: ["instagram_post", "instagram_story", "tiktok_cover"],
  },
  isolated: {
    label: "Assets isolés",
    formats: [
      "symbol_transparent",
      "wordmark_transparent",
      "logo_dark_bg",
      "logo_light_bg",
      "logo_horizontal",
    ],
  },
};

export const ALL_FORMAT_NAMES = Object.values(FORMAT_CATEGORIES).flatMap(
  (cat) => cat.formats
);

export const FORMAT_LABELS: Record<string, string> = {
  instagram_profile: "Instagram profil",
  tiktok_profile: "TikTok profil",
  x_profile: "X profil",
  youtube_profile: "YouTube profil",
  linkedin_profile: "LinkedIn profil",
  favicon: "Favicon",
  app_icon: "App icon",
  x_header: "X header",
  youtube_banner: "YouTube bannière",
  linkedin_banner: "LinkedIn bannière",
  facebook_cover: "Facebook cover",
  instagram_post: "Instagram post",
  instagram_story: "Instagram story",
  tiktok_cover: "TikTok cover",
  symbol_transparent: "Symbol transparent",
  wordmark_transparent: "Wordmark transparent",
  logo_dark_bg: "Logo fond sombre",
  logo_light_bg: "Logo fond clair",
  logo_horizontal: "Logo horizontal",
};

export const FORMAT_DIMENSIONS: Record<string, string> = {
  instagram_profile: "320×320",
  tiktok_profile: "200×200",
  x_profile: "400×400",
  youtube_profile: "800×800",
  linkedin_profile: "300×300",
  favicon: "32×32",
  app_icon: "1024×1024",
  x_header: "1500×500",
  youtube_banner: "2560×1440",
  linkedin_banner: "1128×191",
  facebook_cover: "820×312",
  instagram_post: "1080×1080",
  instagram_story: "1080×1920",
  tiktok_cover: "1080×1920",
  symbol_transparent: "1000×1000",
  wordmark_transparent: "2000×500",
  logo_dark_bg: "1000×1000",
  logo_light_bg: "1000×1000",
  logo_horizontal: "2000×600",
};

export function brandAssetUrl(relativePath: string): string {
  const params = new URLSearchParams({ path: relativePath });
  return hubApiUrl(`/brand/assets?${params.toString()}`);
}

export function brandKitDownloadUrl(kitId: string): string {
  return hubApiUrl(`/brand/kits/${kitId}/download`);
}

async function brandFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  try {
    return await hubFetch<T>(path, { timeoutMs: 120_000, ...options });
  } catch (err) {
    if (err instanceof Error && err.message === "Failed to fetch") {
      throw new Error(
        "Impossible de joindre l'API Hub. Vérifie que le backend tourne."
      );
    }
    throw err;
  }
}

export async function analyzeImage(
  file: File,
  projectId: string
): Promise<BrandAnalyzeResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("project_id", projectId);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 300_000);

  try {
    const res = await fetch(hubApiUrl("/brand/analyze"), {
      method: "POST",
      body: form,
      signal: controller.signal,
      cache: "no-store",
      headers: hubApiKeyHeaders(),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`API ${res.status}: ${text}`);
    }

    return res.json() as Promise<BrandAnalyzeResult>;
  } catch (err) {
    if (err instanceof Error && err.message === "Failed to fetch") {
      throw new Error(
        "Impossible de joindre l'API Hub. Vérifie que le backend tourne."
      );
    }
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error(
        "Analyse interrompue — GPT-4V met trop de temps à répondre."
      );
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function generateKit(
  projectId: string,
  options: {
    kitId?: string | null;
    uploadPath?: string;
    analysis?: BrandAnalysis;
    formats?: string[];
  }
): Promise<BrandGenerateKitResult> {
  return brandFetch<BrandGenerateKitResult>("/brand/generate-kit", {
    method: "POST",
    body: JSON.stringify({
      kit_id: options.kitId ?? null,
      project_id: projectId,
      upload_path: options.uploadPath ?? null,
      analysis: options.analysis ?? null,
      formats: options.formats ?? null,
    }),
    timeoutMs: 600_000,
  });
}

export async function fetchBrandKits(
  projectId?: string
): Promise<BrandKitSummary[]> {
  const query = projectId
    ? `?project_id=${encodeURIComponent(projectId)}`
    : "";
  return brandFetch<BrandKitSummary[]>(`/brand/kits${query}`, {
    timeoutMs: 30_000,
  });
}

export async function fetchBrandKit(kitId: string): Promise<BrandKitDetail> {
  return brandFetch<BrandKitDetail>(`/brand/kits/${kitId}`, {
    timeoutMs: 30_000,
  });
}

export async function downloadKitZip(kitId: string, brandName: string): Promise<void> {
  const response = await fetch(brandKitDownloadUrl(kitId), {
    cache: "no-store",
    headers: hubApiKeyHeaders(),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(`Téléchargement impossible (${response.status}): ${text}`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `brand_kit_${brandName.replace(/\s+/g, "_").toLowerCase()}.zip`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export async function openKitFolder(kitId: string): Promise<void> {
  await brandFetch<{ ok: boolean }>("/brand/open-folder", {
    method: "POST",
    body: JSON.stringify({ kit_id: kitId }),
    timeoutMs: 15_000,
  });
}

export async function fetchBrandReport(reportPath: string): Promise<string> {
  const response = await fetch(brandAssetUrl(reportPath), {
    cache: "no-store",
    headers: hubApiKeyHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Impossible de charger le rapport (${response.status})`);
  }
  return response.text();
}

export interface BrandRefineSegmentsResult {
  kit_id: string;
  analysis: BrandAnalysis;
  segment_paths: Record<string, string>;
  isolated_assets: Record<string, string>;
}

export async function refineSegments(
  kitId: string,
  options: {
    elements: BrandElement[];
    labels?: string[] | null;
    forceBbox?: boolean;
  }
): Promise<BrandRefineSegmentsResult> {
  return brandFetch<BrandRefineSegmentsResult>(
    `/brand/kits/${kitId}/refine-segments`,
    {
      method: "POST",
      body: JSON.stringify({
        elements: options.elements,
        labels: options.labels ?? null,
        force_bbox: options.forceBbox ?? true,
      }),
      timeoutMs: 300_000,
    }
  );
}

export async function downloadAsset(formatName: string, filePath: string): Promise<void> {
  const response = await fetch(brandAssetUrl(filePath), {
    headers: hubApiKeyHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Téléchargement impossible (${response.status})`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${formatName}.png`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

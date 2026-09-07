import { hubFetch } from "./hub-fetch";

export interface BrandColorToken {
  token: string;
  hex: string;
  role: string;
}

export interface BrandDesignSystem {
  ok: boolean;
  source: {
    colors: string;
    kit_id: string | null;
    voice: string;
  };
  color_tokens: BrandColorToken[];
  typography: Record<string, string>;
  layout_tokens?: Record<string, string>;
  voice: Record<string, string>;
  guidelines: string[];
  kit_meta?: {
    mood: string[];
    style: string;
    usage_notes: string;
  };
  reviewers: string[];
}

export interface BrandReviewResult {
  ok: boolean;
  reviewer: string;
  flags: string[];
  voice_ok: boolean;
  department: string;
  sector: string;
  preview: string;
  recommendation: "approve" | "revise" | string;
}

export type BrandDebateRound = {
  round: number;
  agent: string;
  name: string;
  payload: Record<string, unknown>;
};

export type BrandDebateResult = {
  ok: boolean;
  recommendation: "approve" | "revise" | string;
  deliberated: boolean;
  mode: string;
  structural?: BrandReviewResult;
  rounds: BrandDebateRound[];
  debate: {
    verdict?: string;
    elise?: string;
    anouk?: string;
    dissent?: string[];
    actions?: string[];
  } | null;
};

export function fetchDesignSystem() {
  return hubFetch<BrandDesignSystem>("/brand/design-system");
}

export function reviewBrandText(payload: {
  text: string;
  sector?: string;
  department?: string;
}) {
  return hubFetch<BrandReviewResult>("/brand/review", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function debateBrandText(payload: {
  text: string;
  sector?: string;
  department?: string;
  rounds?: number;
}) {
  return hubFetch<BrandDebateResult>("/brand/debate", {
    method: "POST",
    body: JSON.stringify(payload),
    timeoutMs: 90_000,
  });
}

import { hubApiUrl } from "./hub-api-config";
import { hubApiKeyHeaders } from "./hub-api-key";
import { hubFetch } from "./hub-fetch";
import { parseHubApiError } from "./hub-api-error";

export interface GddIngestResult {
  project_id: string;
  document_title: string;
  chunks_count: number;
  sections: string[];
  total_tokens_estimate: number;
}

export interface GddSectionSummary {
  section_title: string;
  chunk_count: number;
  token_estimate: number;
}

export interface GddChunk {
  id: string;
  section_title: string;
  chunk_index: number;
  content: string;
  token_estimate: number;
  document_title?: string;
  source_filename?: string;
}

export interface GddSearchHit {
  id: string;
  section_title: string;
  chunk_index: number;
  snippet: string;
  token_estimate: number;
  score: number;
}

export async function ingestGddFile(
  projectId: string,
  file: File,
  documentTitle = "GDD"
): Promise<GddIngestResult> {
  const form = new FormData();
  form.append("project_id", projectId);
  form.append("document_title", documentTitle);
  form.append("replace_existing", "true");
  form.append("file", file);

  const res = await fetch(hubApiUrl("/gdd/ingest"), {
    method: "POST",
    body: form,
    headers: hubApiKeyHeaders(),
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(parseHubApiError(text, res.status));
  }

  return res.json() as Promise<GddIngestResult>;
}

export async function ingestGddMarkdown(
  projectId: string,
  markdown: string,
  documentTitle = "GDD"
): Promise<GddIngestResult> {
  const form = new FormData();
  form.append("project_id", projectId);
  form.append("document_title", documentTitle);
  form.append("replace_existing", "true");
  form.append("markdown", markdown);

  const res = await fetch(hubApiUrl("/gdd/ingest"), {
    method: "POST",
    body: form,
    headers: hubApiKeyHeaders(),
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(parseHubApiError(text, res.status));
  }

  return res.json() as Promise<GddIngestResult>;
}

export async function fetchGddSections(
  projectId: string
): Promise<GddSectionSummary[]> {
  return hubFetch<GddSectionSummary[]>(`/gdd/${projectId}/sections`, {
    timeoutMs: 15_000,
  });
}

export async function fetchGddChunks(
  projectId: string,
  section?: string
): Promise<GddChunk[]> {
  const params = new URLSearchParams();
  if (section) params.set("section", section);
  const q = params.toString() ? `?${params}` : "";
  return hubFetch<GddChunk[]>(`/gdd/${projectId}/chunks${q}`, {
    timeoutMs: 20_000,
  });
}

export async function searchGdd(
  projectId: string,
  query: string
): Promise<{ query: string; count: number; results: GddSearchHit[] }> {
  return hubFetch(`/gdd/${projectId}/search?q=${encodeURIComponent(query)}`, {
    timeoutMs: 15_000,
  });
}

export async function deleteGddChunks(
  projectId: string
): Promise<{ deleted: boolean }> {
  return hubFetch(`/gdd/${projectId}`, { method: "DELETE", timeoutMs: 10_000 });
}

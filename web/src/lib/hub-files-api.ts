/** Hub user file library — local uploads (not bureau /library archives). */

import { hubFetch } from "./hub-fetch";

export type HubFileSource = "live" | "secretary" | "upload";

export interface HubUserFile {
  id: string;
  name: string;
  size_bytes: number;
  content_type: string;
  source: HubFileSource;
  created_at: string;
  storage_name: string;
}

export async function listHubFiles(params?: {
  q?: string;
  source?: HubFileSource;
  limit?: number;
}): Promise<HubUserFile[]> {
  const qs = new URLSearchParams();
  if (params?.q) qs.set("q", params.q);
  if (params?.source) qs.set("source", params.source);
  if (params?.limit) qs.set("limit", String(params.limit));
  const suffix = qs.size ? `?${qs}` : "";
  const res = await hubFetch<{ files?: HubUserFile[] }>(`/hub/files${suffix}`);
  return res.files ?? [];
}

export async function uploadHubFile(
  file: File,
  source: HubFileSource = "live",
): Promise<HubUserFile> {
  const body = new FormData();
  body.append("file", file);
  body.append("source", source);
  return hubFetch<HubUserFile>("/hub/files", { method: "POST", body });
}

export async function deleteHubFile(fileId: string): Promise<void> {
  await hubFetch(`/hub/files/${encodeURIComponent(fileId)}`, { method: "DELETE" });
}

/** ChatGPT-style: very long paste becomes a .txt attachment instead of filling the prompt. */
export const PASTE_AS_FILE_THRESHOLD = 5000;

export function shouldConvertPasteToFile(charLength: number): boolean {
  return charLength >= PASTE_AS_FILE_THRESHOLD;
}

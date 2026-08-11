import { hubFetch } from "./hub-fetch";

export type NadiaDocMeta = {
  id: string;
  title: string;
  path?: string;
  doc_type?: string;
  updated_at?: string;
};

export type NadiaDoc = NadiaDocMeta & { content?: string };

export function listNadiaDocs(): Promise<{ documents: NadiaDocMeta[] }> {
  return hubFetch("/nadia/docs");
}

export function createNadiaDoc(body: {
  title: string;
  content?: string;
  doc_type?: string;
}): Promise<NadiaDocMeta> {
  return hubFetch("/nadia/docs", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function readNadiaDoc(id: string): Promise<NadiaDoc> {
  return hubFetch(`/nadia/docs/${encodeURIComponent(id)}`);
}

export function updateNadiaDoc(
  id: string,
  body: { content: string; title?: string }
): Promise<NadiaDoc> {
  return hubFetch(`/nadia/docs/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export type HousekeeperStatus = {
  autonomy?: boolean;
  good_reports?: number;
  quarantine_count?: number;
  quarantine_dir?: string;
  roots?: string[];
};

export function housekeeperStatus(): Promise<HousekeeperStatus> {
  return hubFetch("/housekeeper/status");
}

export function housekeeperScan(): Promise<Record<string, unknown>> {
  return hubFetch("/housekeeper/scan", { method: "POST", body: "{}" });
}

export function housekeeperPropose(): Promise<Record<string, unknown>> {
  return hubFetch("/housekeeper/propose", { method: "POST", body: "{}" });
}

export function housekeeperApply(dryRun = false): Promise<Record<string, unknown>> {
  return hubFetch("/housekeeper/apply", {
    method: "POST",
    body: JSON.stringify({ dry_run: dryRun }),
  });
}

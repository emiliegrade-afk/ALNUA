import { hubApiUrl } from "./hub-api-config";

export interface NadiaDesktopStatus {
  hub: { online: boolean; api_url: string };
  last_boot_at?: string;
  boot_count: number;
  greeting_preview: string;
}

export interface NadiaBootResponse {
  greeting: string;
  hub: { online: boolean; api_url: string };
  boot_at: string;
  boot_count: number;
}

export async function fetchNadiaDesktopStatus(): Promise<NadiaDesktopStatus> {
  const res = await fetch(hubApiUrl("/nadia/desktop/status"), { cache: "no-store" });
  if (!res.ok) throw new Error(`Nadia desktop ${res.status}`);
  return res.json() as Promise<NadiaDesktopStatus>;
}

export async function registerNadiaBoot(): Promise<NadiaBootResponse> {
  const res = await fetch(
    hubApiUrl("/nadia/desktop/boot?source=secretary_ui"),
    { method: "POST", cache: "no-store" }
  );
  if (!res.ok) throw new Error(`Nadia boot ${res.status}`);
  return res.json() as Promise<NadiaBootResponse>;
}

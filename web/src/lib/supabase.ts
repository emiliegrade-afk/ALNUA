import { createClient, SupabaseClient } from "@supabase/supabase-js";
import type { AgentLog } from "./types";

let browserClient: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !key) {
    return null;
  }

  if (!browserClient) {
    browserClient = createClient(url, key);
  }

  return browserClient;
}

export async function fetchAgentLogs(limit = 20): Promise<AgentLog[]> {
  const supabase = getSupabase();
  if (!supabase) return [];

  const { data, error } = await supabase
    .from("agent_logs")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("agent_logs fetch:", error.message);
    return [];
  }
  return (data ?? []) as AgentLog[];
}

import { hubFetch } from "@/lib/hub-fetch";

export interface AcademyLevelProgress {
  name: string;
  total: number;
  done: number;
  failed: number;
  in_progress: number;
}

export interface AcademyProgress {
  version: number;
  current_level: number;
  total_exercises: number;
  completed_exercises: number;
  failed_exercises: number;
  success_rate_pct: number;
  levels: Record<string, AcademyLevelProgress>;
  gate_nuaway: Record<string, boolean> & { gate_open?: boolean; readiness_pct?: number };
  last_sprint_at: string | null;
}

export interface AcademyStatus {
  progress: AcademyProgress;
  curriculum_total: number;
  level_meta: Record<string, { name: string; focus: string; issues: number }>;
  github_issues_count: number;
  github_error: string | null;
  repo_configured: boolean;
  repo_path_exists: boolean;
  mem0_snippet: string;
  progress_file: string;
}

export interface AcademySeedResult {
  level: number;
  dry_run: boolean;
  created_count: number;
  skipped_count: number;
  created: Array<{ exercise_id: string; number?: number; url?: string }>;
  skipped: string[];
  github_repo?: string;
}

export async function fetchAcademyStatus(): Promise<AcademyStatus> {
  return hubFetch<AcademyStatus>("/academy/status");
}

export async function seedAcademyLevel(
  level: number,
  options: { dryRun?: boolean; markFirstReady?: boolean } = {}
): Promise<AcademySeedResult> {
  return hubFetch<AcademySeedResult>("/academy/seed", {
    method: "POST",
    body: JSON.stringify({
      level,
      dry_run: options.dryRun ?? false,
      mark_first_ready: options.markFirstReady ?? false,
    }),
    timeoutMs: 120_000,
  });
}

export async function runAcademySprint(
  level: number,
  markReadyCount = 3
): Promise<Record<string, unknown>> {
  return hubFetch<Record<string, unknown>>("/academy/sprint", {
    method: "POST",
    body: JSON.stringify({
      level,
      seed_if_missing: true,
      mark_ready_count: markReadyCount,
    }),
    timeoutMs: 120_000,
  });
}

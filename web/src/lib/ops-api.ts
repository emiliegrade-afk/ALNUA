import { hubFetch } from "@/lib/hub-fetch";

export interface ProductionOpsStatus {
  sentry: {
    tracked_fingerprints: number;
    recent_ingests: Array<{
      fingerprint: string;
      title: string;
      at: string;
      journal_id?: string;
      issue_number?: number;
    }>;
    auto_issue: boolean;
  };
  error_journal: {
    open_count: number;
    summary: string;
  };
  pipeline: {
    bug_watchdog: string;
    poll_issues_loop: string;
  };
  webhook_url: string;
}

export async function fetchProductionOpsStatus(): Promise<ProductionOpsStatus> {
  return hubFetch("/ops/production/status");
}

export async function simulateSentryEvent(options: {
  title: string;
  message?: string;
  projectSlug?: string;
  dryRun?: boolean;
}): Promise<Record<string, unknown>> {
  return hubFetch("/ops/production/simulate", {
    method: "POST",
    body: JSON.stringify({
      title: options.title,
      message: options.message ?? "",
      project_slug: options.projectSlug ?? "hub",
      dry_run: options.dryRun ?? false,
    }),
  });
}

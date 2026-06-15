import { hubFetch } from "./hub-fetch";

export interface AdminFlags {
  environment: string;
  admin_costs_page_enabled: boolean;
  admin_events_page_enabled: boolean;
  admin_ab_test_page_enabled: boolean;
  briefing_coo_section_enabled: boolean;
  briefing_unified_generate: boolean;
  costs_unified_read: boolean;
  costs_shadow_compare: boolean;
  gdd_manager_enabled: boolean;
  preview_allowed: boolean;
}

export async function fetchAdminFlags(): Promise<AdminFlags> {
  return hubFetch<AdminFlags>("/admin/flags", { timeoutMs: 5_000 });
}

export function isAdminPageEnabled(
  flags: AdminFlags | null,
  page: "costs" | "events" | "ab-test",
  preview = false
): boolean {
  if (!flags) return false;
  if (preview && flags.preview_allowed) return true;
  switch (page) {
    case "costs":
      return flags.admin_costs_page_enabled;
    case "events":
      return flags.admin_events_page_enabled;
    case "ab-test":
      return flags.admin_ab_test_page_enabled;
    default:
      return false;
  }
}

export function isBriefingCooSectionEnabled(
  flags: AdminFlags | null,
  preview = false
): boolean {
  if (!flags) return false;
  if (preview && flags.preview_allowed) return true;
  return flags.briefing_coo_section_enabled;
}

export const ADMIN_LINKS: Array<{
  href: string;
  label: string;
  flag: "costs" | "events" | "ab-test";
}> = [
  { href: "/admin/costs", label: "Coûts LLM", flag: "costs" },
  { href: "/admin/events", label: "Event bus", flag: "events" },
  { href: "/admin/ab-test", label: "A/B test", flag: "ab-test" },
];

/** Append ?preview=1 for dev preview navigation (lobby menu, admin hub). */
export function withAdminPreview(href: string, preview: boolean): string {
  if (!preview) return href;
  const sep = href.includes("?") ? "&" : "?";
  return `${href}${sep}preview=1`;
}

export function readAdminPreviewMode(): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("preview") === "1";
}

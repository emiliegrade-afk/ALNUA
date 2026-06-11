export type PostPlatform = "instagram" | "tiktok" | "x" | "youtube" | "linkedin";
export type PostContentType =
  | "announcement"
  | "teaser"
  | "tutorial"
  | "behind_scenes"
  | "short_video"
  | "lore";

export type PostStatus =
  | "draft"
  | "pending_approval"
  | "approved"
  | "published"
  | "failed"
  | "rejected";

export type StatusTab = "pending_approval" | "approved" | "published" | "all";

export const CONTENT_TYPES: { id: PostContentType; label: string }[] = [
  { id: "announcement", label: "Annonce feature" },
  { id: "teaser", label: "Teaser mystère" },
  { id: "behind_scenes", label: "Behind the scenes" },
  { id: "tutorial", label: "Tutoriel court" },
  { id: "short_video", label: "Hype / Engagement" },
  { id: "lore", label: "Lore / Univers" },
];

export const PLATFORMS: { id: PostPlatform; label: string }[] = [
  { id: "instagram", label: "Instagram" },
  { id: "tiktok", label: "TikTok" },
  { id: "x", label: "X" },
  { id: "youtube", label: "YouTube Shorts" },
  { id: "linkedin", label: "LinkedIn" },
];

export const STATUS_TABS: { id: StatusTab; label: string }[] = [
  { id: "pending_approval", label: "À approuver" },
  { id: "approved", label: "Approuvés" },
  { id: "published", label: "Publiés" },
  { id: "all", label: "Tous" },
];

export const PLATFORM_STYLES: Record<
  PostPlatform,
  { badge: string; label: string }
> = {
  instagram: {
    badge: "bg-pink-500/20 text-pink-300 ring-pink-500/30",
    label: "Instagram",
  },
  tiktok: {
    badge: "bg-red-500/20 text-red-300 ring-red-500/30",
    label: "TikTok",
  },
  x: {
    badge: "bg-sky-500/20 text-sky-300 ring-sky-500/30",
    label: "X",
  },
  youtube: {
    badge: "bg-red-600/25 text-red-400 ring-red-600/35",
    label: "YouTube Shorts",
  },
  linkedin: {
    badge: "bg-blue-600/20 text-blue-300 ring-blue-600/30",
    label: "LinkedIn",
  },
};

export const CONTENT_TYPE_LABELS: Record<string, string> = {
  announcement: "Annonce",
  teaser: "Teaser",
  tutorial: "Tutoriel",
  behind_scenes: "Behind the scenes",
  short_video: "Hype",
  lore: "Lore",
};

export const GLOBAL_PROJECT_ID = "__alnua_global__";

export function projectBadgeClass(branch: string, global?: boolean) {
  if (global) return "bg-violet-500/15 text-violet-300 ring-violet-500/25";
  switch (branch) {
    case "app":
      return "bg-naia-muted/50 text-naia-glow ring-naia/30";
    case "gaming":
      return "bg-wyrdheim-muted/50 text-wyrdheim-glow ring-wyrdheim/30";
    case "robotics":
      return "bg-eve-muted/50 text-eve-glow ring-eve/30";
    default:
      return "bg-violet-500/15 text-violet-300 ring-violet-500/25";
  }
}

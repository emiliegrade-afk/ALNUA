import type { CampaignStatus } from "@/lib/marketing-api";
import { C } from "@/app/app-v2/shared";

/* Labels/couleurs de campagnes — extraits de marketing-v2/campagnes-tab.tsx
   (Phase 33) pour être partagés avec le panneau preview de la Vue Globale
   (redesign) sans dupliquer ces 4 Records. */

export const CAMPAIGN_STATUS_LABELS: Record<CampaignStatus, string> = {
  draft: "Brouillon",
  active: "En cours",
  paused: "En pause",
  completed: "Terminée",
};

export const CAMPAIGN_STATUS_COLORS: Record<CampaignStatus, string> = {
  draft: C.faint,
  active: C.online,
  paused: "#E0A95C",
  completed: C.copperLight,
};

export const CAMPAIGN_PLATFORM_LABELS: Record<string, string> = {
  meta: "Meta",
  google: "Google Ads",
  tiktok: "TikTok",
};

export const CAMPAIGN_OBJECTIVE_LABELS: Record<string, string> = {
  awareness: "Notoriété",
  traffic: "Trafic",
  conversions: "Conversions",
  engagement: "Engagement",
  video_views: "Vues vidéo",
};

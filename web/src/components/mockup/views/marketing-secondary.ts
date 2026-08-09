type ListRow = { primary: string; secondary?: string; meta?: string; tone?: "ok" | "warn" | "muted" };

export type MarketingPanelDef = {
  title: string;
  subtitle: string;
  stats: { label: string; value: string }[];
  left: { title: string; rows: ListRow[] };
  right: { title: string; rows: ListRow[] };
};

export const MARKETING_SECONDARY: Record<string, MarketingPanelDef> = {
  campagnes: {
    title: "Campagnes",
    subtitle: "Campagnes actives et performance ROI",
    stats: [
      { label: "Actives", value: "4" },
      { label: "Budget", value: "8.6k€" },
      { label: "ROI moy.", value: "3.5x" },
      { label: "Leads", value: "712" },
      { label: "CA", value: "18.2k€" },
    ],
    left: {
      title: "CAMPAGNES ACTIVES",
      rows: [
        { primary: "Lancement NAÏA", secondary: "Instagram · 2.4k€", meta: "4.2x", tone: "ok" },
        { primary: "NUAWAY Summer", secondary: "TikTok · 1.8k€", meta: "3.8x", tone: "ok" },
        { primary: "Brand ALNUA", secondary: "LinkedIn · 3.2k€", meta: "2.9x", tone: "ok" },
        { primary: "EVE Demo", secondary: "YouTube · 1.2k€", meta: "3.1x", tone: "ok" },
      ],
    },
    right: {
      title: "À LANCER",
      rows: [
        { primary: "RESONANCE soft launch", secondary: "Meta Ads · brief prêt", meta: "Q3", tone: "warn" },
        { primary: "Retargeting Hub", secondary: "Google · audiences chaudes", meta: "Août", tone: "muted" },
        { primary: "Newsletter back-to-school", secondary: "Email · freelances", meta: "Sept.", tone: "muted" },
      ],
    },
  },
  content: {
    title: "Content Studio",
    subtitle: "Pipeline éditorial multi-pôles",
    stats: [
      { label: "En file", value: "18" },
      { label: "Publiés 7j", value: "24" },
      { label: "Drafts", value: "9" },
      { label: "Validés", value: "6" },
      { label: "Reach top", value: "128K" },
    ],
    left: {
      title: "TOP CONTENUS",
      rows: [
        { primary: "Behind the scenes NAÏA", secondary: "Reel Instagram", meta: "128K", tone: "ok" },
        { primary: "EVE demo reel", secondary: "YouTube", meta: "96K", tone: "ok" },
        { primary: "NOMAD journey", secondary: "TikTok", meta: "84K", tone: "ok" },
        { primary: "ALNUA manifesto", secondary: "LinkedIn", meta: "58K", tone: "muted" },
      ],
    },
    right: {
      title: "EN PRODUCTION",
      rows: [
        { primary: "Carrousel skills Hub", secondary: "Sofia · Instagram", meta: "Draft", tone: "warn" },
        { primary: "Thread R&D incubateur", secondary: "Anouk · LinkedIn", meta: "Revue", tone: "warn" },
        { primary: "Short Gaming Studio", secondary: "Kael · TikTok", meta: "Tournage", tone: "muted" },
      ],
    },
  },
  social: {
    title: "Social Media",
    subtitle: "Présence organique et calendrier",
    stats: [
      { label: "Followers", value: "86.4K" },
      { label: "+7j", value: "+2.1K" },
      { label: "Eng. moy.", value: "7.8%" },
      { label: "Posts/sem.", value: "14" },
      { label: "Stories", value: "22" },
    ],
    left: {
      title: "CANAUX",
      rows: [
        { primary: "Instagram", secondary: "540K reach · eng. 8.2%", meta: "Lead", tone: "ok" },
        { primary: "TikTok", secondary: "420K reach · eng. 12.4%", meta: "Croissance", tone: "ok" },
        { primary: "LinkedIn", secondary: "180K reach · eng. 5.6%", meta: "B2B", tone: "muted" },
        { primary: "YouTube", secondary: "210K reach · eng. 6.1%", meta: "Stable", tone: "muted" },
      ],
    },
    right: {
      title: "AUJOURD'HUI",
      rows: [
        { primary: "08:00 Instagram Post", secondary: "Publié", meta: "OK", tone: "ok" },
        { primary: "14:00 TikTok", secondary: "En cours", meta: "Live", tone: "warn" },
        { primary: "17:00 LinkedIn", secondary: "Programmé", meta: "Queue", tone: "muted" },
        { primary: "20:00 Threads", secondary: "Programmé", meta: "Queue", tone: "muted" },
      ],
    },
  },
  seo: {
    title: "SEO",
    subtitle: "Visibilité organique et contenu evergreen",
    stats: [
      { label: "Mots-clés", value: "142" },
      { label: "Top 10", value: "28" },
      { label: "Trafic org.", value: "18.4K" },
      { label: "Pages", value: "36" },
      { label: "Score tech", value: "91" },
    ],
    left: {
      title: "PAGES PERFORMANTES",
      rows: [
        { primary: "/blog/agents-llm-ops", secondary: "Position 4 · +1.2K visites", meta: "↑", tone: "ok" },
        { primary: "/produits/naia", secondary: "Position 7 · intent commercial", meta: "↑", tone: "ok" },
        { primary: "/hub/docs", secondary: "Position 11 · longue traîne", meta: "→", tone: "muted" },
      ],
    },
    right: {
      title: "OPPORTUNITÉS",
      rows: [
        { primary: "Cluster agent orchestration", secondary: "Gaps vs concurrent", meta: "Priorité", tone: "warn" },
        { primary: "FAQ NAÏA wellness", secondary: "Featured snippets cibles", meta: "Août", tone: "muted" },
        { primary: "Internal linking Hub", secondary: "12 orphelines détectées", meta: "Quick win", tone: "ok" },
      ],
    },
  },
  ads: {
    title: "Ads",
    subtitle: "Publicité payante Meta · Google · TikTok",
    stats: [
      { label: "Spend 30j", value: "6.8k€" },
      { label: "ROAS", value: "3.4x" },
      { label: "CPA", value: "24€" },
      { label: "CTR", value: "2.9%" },
      { label: "Conv.", value: "284" },
    ],
    left: {
      title: "COMPTES ACTIFS",
      rows: [
        { primary: "Meta Ads — NAÏA", secondary: "Prospecting + retarget", meta: "2.1k€", tone: "ok" },
        { primary: "Google Search — Hub", secondary: "Brand + génériques", meta: "1.9k€", tone: "ok" },
        { primary: "TikTok — NUAWAY", secondary: "Spark Ads créateurs", meta: "1.6k€", tone: "ok" },
        { primary: "LinkedIn — ALNUA", secondary: "Thought leadership", meta: "1.2k€", tone: "muted" },
      ],
    },
    right: {
      title: "ALERTES LÉO",
      rows: [
        { primary: "Fréquence Meta > 3.2", secondary: "Créas à renouveler", meta: "Attention", tone: "warn" },
        { primary: "CPA Google en baisse", secondary: "−18% vs semaine préc.", meta: "OK", tone: "ok" },
        { primary: "Budget TikTok 82%", secondary: "Recharge avant vendredi", meta: "Watch", tone: "warn" },
      ],
    },
  },
  analytics: {
    title: "Analytics",
    subtitle: "Mesure multi-canal et attribution",
    stats: [
      { label: "Reach", value: "1.24M" },
      { label: "Conv.", value: "4.8%" },
      { label: "CA", value: "18.2k€" },
      { label: "ROI", value: "287%" },
      { label: "Sessions", value: "152K" },
    ],
    left: {
      title: "FUNNEL",
      rows: [
        { primary: "Visiteurs", secondary: "152 480", meta: "100%", tone: "muted" },
        { primary: "Intéressés", secondary: "28 450", meta: "18.7%", tone: "ok" },
        { primary: "Engagés", secondary: "9 622", meta: "6.3%", tone: "ok" },
        { primary: "Clients", secondary: "712", meta: "0.5%", tone: "ok" },
      ],
    },
    right: {
      title: "ATTRIBUTION",
      rows: [
        { primary: "Instagram → essai NAÏA", secondary: "Last-click dominant", meta: "38%", tone: "ok" },
        { primary: "SEO → Hub demo", secondary: "Assisted conversions", meta: "22%", tone: "ok" },
        { primary: "Email → upgrade", secondary: "Nurture Série B", meta: "17%", tone: "muted" },
      ],
    },
  },
  auto: {
    title: "Automatisation",
    subtitle: "Workflows n8n et publications planifiées",
    stats: [
      { label: "Flows actifs", value: "11" },
      { label: "Runs 24h", value: "86" },
      { label: "Échecs", value: "2" },
      { label: "Slots", value: "48" },
      { label: "Uptime", value: "99.1%" },
    ],
    left: {
      title: "WORKFLOWS",
      rows: [
        { primary: "Publish social queue", secondary: "n8n · IG/TikTok/LI", meta: "OK", tone: "ok" },
        { primary: "Brief → Sofia draft", secondary: "Webhook Hub → Content", meta: "OK", tone: "ok" },
        { primary: "Ads spend alert", secondary: "Budget > 85% → Léo", meta: "OK", tone: "ok" },
        { primary: "Weekly digest Camille", secondary: "Lundi 08:00", meta: "2 fails", tone: "warn" },
      ],
    },
    right: {
      title: "FILE PROGRAMMÉE",
      rows: [
        { primary: "Carrousel NAÏA · IG", secondary: "Demain 09:00", meta: "Queued", tone: "muted" },
        { primary: "Reel EVE · TikTok", secondary: "Demain 18:30", meta: "Queued", tone: "muted" },
        { primary: "Newsletter Hub", secondary: "Mercredi 10:00", meta: "Draft", tone: "warn" },
      ],
    },
  },
  brand: {
    title: "Brand Center",
    subtitle: "Alignement marque et assets marketing",
    stats: [
      { label: "Kits liés", value: "4" },
      { label: "Assets MKT", value: "36" },
      { label: "Templates", value: "12" },
      { label: "Compliance", value: "94%" },
      { label: "Revues", value: "3" },
    ],
    left: {
      title: "ASSETS CAMPAGNES",
      rows: [
        { primary: "Pack NAÏA Stories", secondary: "9 frames · charte validée", meta: "OK", tone: "ok" },
        { primary: "Thumbnails YouTube EVE", secondary: "Cuivre + ivoire", meta: "OK", tone: "ok" },
        { primary: "Bannières LinkedIn ALNUA", secondary: "3 variantes", meta: "Revue", tone: "warn" },
      ],
    },
    right: {
      title: "GARDES-FOUS",
      rows: [
        { primary: "Pas de violet générique", secondary: "Accent = cuivre uniquement", meta: "Strict", tone: "ok" },
        { primary: "Logo sur fond sombre", secondary: "Ivoire ou cuivre", meta: "Strict", tone: "ok" },
        { primary: "Claims santé NAÏA", secondary: "Validation legal avant pub", meta: "Watch", tone: "warn" },
      ],
    },
  },
};

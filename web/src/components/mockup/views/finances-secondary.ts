type ListRow = { primary: string; secondary?: string; meta?: string; tone?: "ok" | "warn" | "muted" };

export type FinancesPanelDef = {
  title: string;
  subtitle: string;
  stats: { label: string; value: string }[];
  left: { title: string; rows: ListRow[] };
  right: { title: string; rows: ListRow[] };
};

export const FINANCES_SECONDARY: Record<string, FinancesPanelDef> = {
  Transactions: {
    title: "Transactions",
    subtitle: "Flux entrants / sortants · 30 derniers jours",
    stats: [
      { label: "Entrées", value: "12.4k€" },
      { label: "Sorties", value: "4.8k€" },
      { label: "Net", value: "+7.6k€" },
      { label: "Ops", value: "48" },
      { label: "En attente", value: "3" },
    ],
    left: {
      title: "RÉCENTES",
      rows: [
        { primary: "Paiement client NAÏA", secondary: "07/08 · Stripe", meta: "+2 400 €", tone: "ok" },
        { primary: "Facture hosting", secondary: "06/08 · OVH", meta: "−340 €", tone: "warn" },
        { primary: "Adspend Meta", secondary: "05/08 · Ads", meta: "−1 200 €", tone: "warn" },
        { primary: "Prestation NUAWAY", secondary: "04/08 · Virement", meta: "+1 800 €", tone: "ok" },
      ],
    },
    right: {
      title: "À RÉCONCILIER",
      rows: [
        { primary: "Frais Cursor IDE", secondary: "Carte · 80 €", meta: "Review", tone: "muted" },
        { primary: "Remboursement freelances", secondary: "3 notes de frais", meta: "420 €", tone: "warn" },
        { primary: "Acompte RESONANCE", secondary: "Devis signé", meta: "Attendu", tone: "muted" },
      ],
    },
  },
  Budgets: {
    title: "Budgets",
    subtitle: "Enveloppes par pôle · burn vs plafond",
    stats: [
      { label: "Total alloué", value: "536k€" },
      { label: "Consommé", value: "264k€" },
      { label: "Reste", value: "272k€" },
      { label: "Alertes", value: "2" },
      { label: "Burn moy.", value: "420€/mo" },
    ],
    left: {
      title: "PAR PÔLE",
      rows: [
        { primary: "APP", secondary: "68 / 120k€", meta: "57%", tone: "ok" },
        { primary: "Gaming", secondary: "38 / 95k€", meta: "40%", tone: "ok" },
        { primary: "Robotique", secondary: "45 / 110k€", meta: "41%", tone: "ok" },
        { primary: "Marketing", secondary: "41 / 85k€", meta: "48%", tone: "ok" },
        { primary: "R&D", secondary: "72 / 126k€", meta: "57%", tone: "warn" },
      ],
    },
    right: {
      title: "ALERTES",
      rows: [
        { primary: "OpenRouter tokens", secondary: "Dépassement semaine", meta: "+12%", tone: "warn" },
        { primary: "Ads Meta août", secondary: "Plafond 80% atteint", meta: "Watch", tone: "warn" },
        { primary: "Hardware BOM EVE", secondary: "Sous enveloppe", meta: "OK", tone: "ok" },
      ],
    },
  },
  Prévisions: {
    title: "Prévisions",
    subtitle: "Cash runway · scénarios 90 jours",
    stats: [
      { label: "Runway", value: "97 mo" },
      { label: "Cash 90j", value: "71k€" },
      { label: "MRR cible", value: "6.2k€" },
      { label: "Scénario A", value: "+14%" },
      { label: "Scénario B", value: "+6%" },
    ],
    left: {
      title: "HYPOTHÈSES",
      rows: [
        { primary: "NAÏA conversion +1.2pt", secondary: "Funnel Q3", meta: "Base", tone: "ok" },
        { primary: "Ads CAC stable", secondary: "Meta + Google", meta: "Base", tone: "ok" },
        { primary: "Hiring pause", secondary: "Aucun CDI Q3", meta: "Conso", tone: "muted" },
      ],
    },
    right: {
      title: "JALONS CASH",
      rows: [
        { primary: "TVA Q2", secondary: "Échéance J+16", meta: "3 240 €", tone: "warn" },
        { primary: "Renewal OpenAI", secondary: "Mensuel", meta: "480 €", tone: "muted" },
        { primary: "Milestone NUAWAY", secondary: "Facture à émettre", meta: "4.5k€", tone: "ok" },
      ],
    },
  },
  Facturation: {
    title: "Facturation",
    subtitle: "MRR · factures clients · encaissements",
    stats: [
      { label: "MRR", value: "4 850 €" },
      { label: "Ouvertes", value: "7" },
      { label: "Payées 30j", value: "18" },
      { label: "Retard", value: "2" },
      { label: "ARR", value: "58.2k€" },
    ],
    left: {
      title: "FACTURES OUVERTES",
      rows: [
        { primary: "NAÏA — abo Pro", secondary: "INV-2041 · 15j", meta: "890 €", tone: "ok" },
        { primary: "NUAWAY — sprint", secondary: "INV-2038 · 8j", meta: "2 400 €", tone: "warn" },
        { primary: "EVE — proto kit", secondary: "INV-2035 · 22j", meta: "1 200 €", tone: "muted" },
      ],
    },
    right: {
      title: "ABONNEMENTS",
      rows: [
        { primary: "OpenAI", secondary: "Mensuel", meta: "480 €", tone: "muted" },
        { primary: "Claude", secondary: "Mensuel", meta: "220 €", tone: "muted" },
        { primary: "Cursor IDE", secondary: "Mensuel", meta: "80 €", tone: "muted" },
      ],
    },
  },
  Fiscalité: {
    title: "Fiscalité",
    subtitle: "TVA · URSSAF · échéances",
    stats: [
      { label: "TVA due", value: "3 240 €" },
      { label: "Jours restants", value: "16" },
      { label: "Cotisations", value: "890 €" },
      { label: "Déclarations", value: "3" },
      { label: "Statut", value: "OK" },
    ],
    left: {
      title: "ÉCHÉANCES",
      rows: [
        { primary: "TVA à déclarer", secondary: "J+16", meta: "3 240 €", tone: "warn" },
        { primary: "Cotisations sociales", secondary: "J+12", meta: "890 €", tone: "warn" },
        { primary: "CFE estimée", secondary: "Annuelle", meta: "1 100 €", tone: "muted" },
      ],
    },
    right: {
      title: "DOSSIERS",
      rows: [
        { primary: "Export FEC Q2", secondary: "Prêt export", meta: "OK", tone: "ok" },
        { primary: "Justificatifs ads", secondary: "2 manquants", meta: "Action", tone: "warn" },
        { primary: "Note comptable LLM", secondary: "Jules · draft", meta: "Revue", tone: "muted" },
      ],
    },
  },
  Salaires: {
    title: "Salaires",
    subtitle: "Masse · freelances · charges",
    stats: [
      { label: "Masse mois", value: "0 €" },
      { label: "Freelances", value: "2.1k€" },
      { label: "Charges", value: "420 €" },
      { label: "Notes frais", value: "3" },
      { label: "Paie", value: "N/A" },
    ],
    left: {
      title: "FREELANCES",
      rows: [
        { primary: "Design UI Hub", secondary: "Mission Août", meta: "900 €", tone: "ok" },
        { primary: "Sound design EVE", secondary: "Gaming", meta: "650 €", tone: "ok" },
        { primary: "Copy landing NAÏA", secondary: "Marketing", meta: "550 €", tone: "muted" },
      ],
    },
    right: {
      title: "NOTES DE FRAIS",
      rows: [
        { primary: "Matériel proto", secondary: "Hardware", meta: "180 €", tone: "warn" },
        { primary: "Abonnement Figma", secondary: "Brand", meta: "45 €", tone: "muted" },
        { primary: "Déplacement meetup", secondary: "CEO", meta: "95 €", tone: "muted" },
      ],
    },
  },
  Investissements: {
    title: "Investissements",
    subtitle: "ROI campagnes · R&D · assets",
    stats: [
      { label: "Investi", value: "13.5k€" },
      { label: "ROI moy.", value: "270%" },
      { label: "Actifs", value: "3" },
      { label: "En veille", value: "2" },
      { label: "Profit mois", value: "18.2k€" },
    ],
    left: {
      title: "PORTEFEUILLE",
      rows: [
        { primary: "Campagne Ads été", secondary: "Marketing", meta: "380%", tone: "ok" },
        { primary: "NAÏA V2", secondary: "APP", meta: "280%", tone: "ok" },
        { primary: "Robot Companion", secondary: "Hardware", meta: "150%", tone: "ok" },
      ],
    },
    right: {
      title: "PIPELINE",
      rows: [
        { primary: "RESONANCE soft launch", secondary: "Budget à valider", meta: "Q3", tone: "warn" },
        { primary: "Incubateur dossier #12", secondary: "Conseil R&D", meta: "Vote", tone: "muted" },
        { primary: "Godot vertical slice", secondary: "Gaming", meta: "Hold", tone: "muted" },
      ],
    },
  },
};

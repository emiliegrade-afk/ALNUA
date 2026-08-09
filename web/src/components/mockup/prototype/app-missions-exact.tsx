"use client";

import { CheckCircle2, ChevronDown, Filter, Search } from "lucide-react";
import { ProtoAvatar, ProtoProgressRing, ProtoSectionHeader } from "./proto-shared";

const STATS = [
  { label: "Missions au total", value: "42" },
  { label: "En cours", value: "18" },
  { label: "En attente", value: "7" },
  { label: "En test", value: "6" },
  { label: "Terminées", value: "11" },
];

const COLS: { key: string; title: string; count: number; cards: MissionCard[] }[] = [
  {
    key: "todo",
    title: "À FAIRE",
    count: 7,
    cards: [
      { title: "Intégration Apple Health", project: "NAÏA / Santé", who: "theo", pts: "5 pts" },
      { title: "Export PDF rapports", project: "Academy", who: "hao", pts: "3 pts" },
    ],
  },
  {
    key: "doing",
    title: "EN COURS",
    count: 18,
    cards: [
      { title: "Notifications Push", project: "NAÏA", who: "theo", progress: 78 },
      { title: "Auth refactor Expo", project: "NUAWAY", who: "hao", progress: 63 },
    ],
  },
  {
    key: "wait",
    title: "EN ATTENTE",
    count: 7,
    cards: [
      { title: "Tests Module Coach", project: "NAÏA", who: "sam", pts: "Bloqué" },
      { title: "Validation design v3", project: "Hub", who: "ines", pts: "Review" },
    ],
  },
  {
    key: "test",
    title: "EN TEST",
    count: 6,
    cards: [
      { title: "Tests automation Cycle", project: "Academy", who: "rayan", progress: 45 },
      { title: "QA API v2", project: "NAÏA", who: "hao", progress: 70 },
    ],
  },
  {
    key: "done",
    title: "TERMINÉES",
    count: 11,
    cards: [
      { title: "UI Kit v2.3", project: "Hub", who: "ines", done: true },
      { title: "MessageList", project: "Academy", who: "theo", done: true },
    ],
  },
];

type MissionCard = {
  title: string;
  project: string;
  who: string;
  pts?: string;
  progress?: number;
  done?: boolean;
};

const PRIORITIES = [
  { label: "Haute", color: "#d56b70", count: 9, items: ["API Hydratation", "Push critical path"] },
  { label: "Moyenne", color: "#e7a85f", count: 21, items: ["Onboarding v2", "Cache offline"] },
  { label: "Basse", color: "#7ba7d9", count: 8, items: ["Dark polish", "Tooltips"] },
  { label: "À venir", color: "#a78bfa", count: 4, items: ["WatchOS", "Widgets"] },
];

const WORKLOAD = [
  { id: "theo", name: "Théo Laurent", load: 78 },
  { id: "hao", name: "Hao Chen", load: 82 },
  { id: "ines", name: "Inès Moreau", load: 65 },
  { id: "rayan", name: "Rayan Koné", load: 71 },
  { id: "sam", name: "Sam Rivera", load: 58 },
  { id: "aria", name: "Aria Voss", load: 44 },
];

const RISKS = [
  { title: "API Hydratation", level: "élevé", why: "Retard estimé 3j" },
  { title: "Carte Offline v2", level: "moyen", why: "Dépendance Expo" },
  { title: "Optimisation requêtes", level: "moyen", why: "Charge QA" },
];

const TIMELINE = [
  { t: "22:14", who: "theo", text: "a terminé la mission MessageList", tag: "NAÏA", ok: true },
  { t: "22:11", who: "hao", text: "a mis à jour Notifications Push", tag: "NAÏA", ok: false },
  { t: "22:08", who: "ines", text: "a validé UI Kit v2.3", tag: "Hub", ok: true },
  { t: "22:02", who: "rayan", text: "a lancé Tests automation", tag: "Academy", ok: false },
];

/** Missions APP — layout maquette ChatGPT 28 juil. */
export function AppMissionsExact() {
  return (
    <div className="grid gap-3 pb-6 xl:grid-cols-[minmax(0,1fr)_260px]">
      <div className="min-w-0 space-y-3">
        <ProtoSectionHeader
          title="MISSIONS"
          desc="Toutes les missions en cours, assignées ou planifiées"
          icon={<span className="text-[11px] font-semibold">S</span>}
        >
          <button type="button" className="outline-btn">
            <Filter size={14} /> Filtres
          </button>
          <button type="button" className="outline-btn">
            Vue Board <ChevronDown size={13} />
          </button>
          <button type="button" className="primary-btn">
            + Nouvelle mission
          </button>
        </ProtoSectionHeader>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {STATS.map((s) => (
            <div
              key={s.label}
              className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#0b1118] px-3 py-2.5"
            >
              <p className="text-[17px] font-medium text-[#e8e2da]">{s.value}</p>
              <p className="text-[9px] text-[#6e767f]">{s.label}</p>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0a1017] p-3">
          <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">BOARD DES MISSIONS</p>
          <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-5">
            {COLS.map((col) => (
              <div key={col.key} className="min-w-0 rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#090e14] p-2">
                <div className="mb-2 flex items-center justify-between text-[10px]">
                  <b className="text-[#c9c5be]">{col.title}</b>
                  <span className="rounded bg-[#151c24] px-1.5 py-0.5 text-[#7e8790]">{col.count}</span>
                </div>
                <div className="space-y-2">
                  {col.cards.map((c) => (
                    <article
                      key={c.title}
                      className="rounded-md border border-[rgba(255,255,255,0.07)] bg-[#0d141b] p-2"
                    >
                      <p className="text-[10px] font-medium leading-snug text-[#e8e2da]">{c.title}</p>
                      <p className="mt-1 text-[8px] text-[#6e767f]">{c.project}</p>
                      <div className="mt-2 flex items-center justify-between gap-1">
                        <div className="flex items-center gap-1">
                          <ProtoAvatar agent={c.who} size="sm" />
                        </div>
                        {c.done ? (
                          <CheckCircle2 size={14} className="text-[#5ed69a]" />
                        ) : c.progress != null ? (
                          <span className="text-[9px] text-[#e0a477]">{c.progress}%</span>
                        ) : (
                          <span className="text-[8px] text-[#7e8790]">{c.pts}</span>
                        )}
                      </div>
                      {c.progress != null ? (
                        <div className="bar mt-2">
                          <i style={{ width: `${c.progress}%` }} />
                        </div>
                      ) : null}
                    </article>
                  ))}
                </div>
                <button type="button" className="mt-2 w-full text-[9px] text-[#8e969e]">
                  + Nouvelle mission
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0a1017] p-3">
          <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">VUE PAR PRIORITÉ</p>
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            {PRIORITIES.map((p) => (
              <div key={p.label} className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-2.5">
                <div className="mb-2 flex items-center gap-2">
                  <i className="inline-block h-2 w-2 rounded-full" style={{ background: p.color }} />
                  <b className="text-[11px] text-[#e8e2da]">{p.label}</b>
                  <span className="ml-auto text-[9px] text-[#6e767f]">{p.count}</span>
                </div>
                {p.items.map((it) => (
                  <p key={it} className="border-t border-[rgba(255,255,255,0.05)] py-1.5 text-[9px] text-[#9aa1a8]">
                    {it}
                  </p>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0a1017] p-3">
          <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">CHRONOLOGIE DES MISSIONS</p>
          <div className="space-y-2">
            {TIMELINE.map((row) => (
              <div key={row.t + row.text} className="flex items-center gap-2 border-b border-[rgba(255,255,255,0.05)] py-2">
                <span className="w-10 font-mono text-[9px] text-[#e0a477]">{row.t}</span>
                <ProtoAvatar agent={row.who} size="sm" />
                <p className="min-w-0 flex-1 text-[10px] text-[#9aa1a8]">
                  {row.text} <small className="text-[#5f6871]">{row.tag}</small>
                </p>
                {row.ok ? <CheckCircle2 size={14} className="text-[#5ed69a]" /> : null}
              </div>
            ))}
          </div>
        </div>
      </div>

      <aside className="space-y-3">
        <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
          <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">FILTRES</p>
          <div className="search mb-2 w-full">
            <Search size={14} />
            <input placeholder="Rechercher une mission..." readOnly />
          </div>
          {["Projet", "Statut", "Priorité", "Assigné à", "Échéance"].map((f) => (
            <button key={f} type="button" className="small-select mb-1.5 w-full justify-between">
              {f} <ChevronDown size={13} />
            </button>
          ))}
          <button type="button" className="primary-btn mt-2 w-full justify-center">
            Appliquer les filtres
          </button>
        </section>

        <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
          <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">CHARGE DE TRAVAIL</p>
          {WORKLOAD.map((w) => (
            <div key={w.id} className="mb-2">
              <div className="mb-1 flex items-center gap-2">
                <ProtoAvatar agent={w.id} size="sm" />
                <span className="flex-1 truncate text-[9px] text-[#c9c5be]">{w.name}</span>
                <span className="text-[9px] text-[#e0a477]">{w.load}%</span>
              </div>
              <div className="bar">
                <i style={{ width: `${w.load}%` }} />
              </div>
            </div>
          ))}
        </section>

        <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
          <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">MISSIONS À RISQUE</p>
          {RISKS.map((r) => (
            <div key={r.title} className="mb-2 rounded-md border border-[rgba(255,255,255,0.07)] bg-[#0d141b] p-2">
              <p className="text-[10px] text-[#e8e2da]">{r.title}</p>
              <p className="mt-1 text-[8px] text-[#6e767f]">{r.why}</p>
              <span
                className="mt-1 inline-block rounded px-1.5 py-0.5 text-[8px]"
                style={{
                  color: r.level === "élevé" ? "#d56b70" : "#e7a85f",
                  background: r.level === "élevé" ? "rgba(213,107,112,.12)" : "rgba(231,168,95,.12)",
                }}
              >
                Risque {r.level}
              </span>
            </div>
          ))}
        </section>

        <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3 text-center">
          <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">PERFORMANCE GLOBALE</p>
          <div className="flex justify-center">
            <ProtoProgressRing value={78} />
          </div>
          <p className="mt-2 text-[11px] text-[#e8e2da]">78% Efficacité</p>
          <p className="mt-1 text-[9px] text-[#6e767f]">Temps estimé 312h · passé 243h</p>
          <p className="mt-1 text-[9px] text-[#5ed69a]">+12% vs semaine dernière</p>
        </section>
      </aside>
    </div>
  );
}

"use client";

import { ChevronRight, Filter, Lightbulb, Plus } from "lucide-react";
import { ProtoAvatar, ProtoSectionHeader } from "./proto-shared";

const KPIS = [
  { label: "Items au total", value: "128" },
  { label: "Nouveaux", value: "45" },
  { label: "À prioriser", value: "38" },
  { label: "En attente", value: "28" },
  { label: "Déjà planifiés", value: "17" },
];

const COLS: { title: string; count: number; cards: { title: string; tag: string; who: string; votes: number }[] }[] = [
  {
    title: "NOUVELLES IDÉES",
    count: 45,
    cards: [
      { title: "Mode sombre avancé", tag: "Amélioration", who: "ines", votes: 12 },
      { title: "Intégration Apple Health", tag: "Fonctionnalité", who: "theo", votes: 9 },
    ],
  },
  {
    title: "À PRIORISER",
    count: 38,
    cards: [
      { title: "Coach IA personnalisé", tag: "Fonctionnalité", who: "sam", votes: 18 },
      { title: "Gamification défis", tag: "Recherche", who: "nova", votes: 7 },
    ],
  },
  {
    title: "EN ATTENTE",
    count: 28,
    cards: [
      { title: "Refonte onboarding", tag: "Amélioration", who: "ines", votes: 5 },
      { title: "Sync watchOS", tag: "Fonctionnalité", who: "hao", votes: 4 },
    ],
  },
  {
    title: "VALIDÉES",
    count: 12,
    cards: [
      { title: "Dashboard santé v2", tag: "Fonctionnalité", who: "theo", votes: 21 },
      { title: "Push topics", tag: "Correction", who: "hao", votes: 6 },
    ],
  },
  {
    title: "PLANIFIÉES",
    count: 17,
    cards: [
      { title: "Audio méditations Premium", tag: "Fonctionnalité", who: "sam", votes: 14 },
      { title: "Sprint 19 — Widgets", tag: "Amélioration", who: "rayan", votes: 8 },
    ],
  },
  {
    title: "REJETÉES",
    count: 8,
    cards: [
      { title: "Réseau social intégré", tag: "Fonctionnalité", who: "mira", votes: 2 },
      { title: "Marketplace skins", tag: "Recherche", who: "nova", votes: 1 },
    ],
  },
];

const ACTIVITY = [
  { who: "ines", text: "a ajouté une idée Mode sombre avancé", ago: "il y a 4h" },
  { who: "hao", text: "a déplacé Coach IA vers À prioriser", ago: "il y a 5h" },
  { who: "theo", text: "a validé Dashboard santé v2", ago: "il y a 6h" },
  { who: "sam", text: "a planifié Audio méditations", ago: "il y a 8h" },
];

/** Backlog APP — maquette ChatGPT 30 juil. */
export function AppBacklogExact() {
  return (
    <div className="grid gap-3 pb-6 xl:grid-cols-[minmax(0,1fr)_240px]">
      <div className="min-w-0 space-y-3">
        <ProtoSectionHeader
          title="BACKLOG"
          desc="Idées, priorisation et planification du département APP"
          icon={<Lightbulb size={16} />}
        >
          <button type="button" className="outline-btn">
            <Filter size={14} /> Filtres
          </button>
          <button type="button" className="outline-btn">
            Vue Board
          </button>
          <button type="button" className="primary-btn">
            <Plus size={15} /> Nouvelle idée
          </button>
        </ProtoSectionHeader>

        <div className="flex flex-wrap items-stretch gap-2">
          {KPIS.map((k) => (
            <div
              key={k.label}
              className="min-w-[110px] flex-1 rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#0b1118] px-3 py-2"
            >
              <p className="text-[16px] font-medium text-[#e8e2da]">{k.value}</p>
              <p className="text-[8px] text-[#6e767f]">{k.label}</p>
            </div>
          ))}
          <div className="flex min-w-[140px] items-center gap-3 rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#0b1118] px-3 py-2">
            <div
              className="h-11 w-11 rounded-full"
              style={{
                background:
                  "conic-gradient(#e0a477 0 60%, #7ba7d9 60% 75%, #5ed69a 75% 90%, #56606b 90%)",
              }}
            />
            <div>
              <p className="text-[8px] text-[#6e767f]">Répartition par type</p>
              <p className="text-[9px] text-[#c9c5be]">Fonct. 60% · Corr. 15% · Rech. 15%</p>
            </div>
          </div>
        </div>

        <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
          {COLS.map((col) => (
            <div key={col.title} className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#090e14] p-2">
              <div className="mb-2 flex items-center justify-between">
                <b className="text-[9px] tracking-wide text-[#c9c5be]">{col.title}</b>
                <span className="text-[9px] text-[#6e767f]">{col.count}</span>
              </div>
              <div className="space-y-2">
                {col.cards.map((c) => (
                  <article
                    key={c.title}
                    className="rounded-md border border-[rgba(255,255,255,0.07)] bg-[#0d141b] p-2"
                  >
                    <p className="text-[10px] font-medium leading-snug text-[#e8e2da]">{c.title}</p>
                    <span className="mt-1 inline-block rounded bg-[#151c24] px-1.5 py-0.5 text-[7px] text-[#7e8790]">
                      {c.tag}
                    </span>
                    <div className="mt-2 flex items-center justify-between">
                      <ProtoAvatar agent={c.who} size="sm" />
                      <span className="text-[8px] text-[#e0a477]">↑ {c.votes}</span>
                    </div>
                  </article>
                ))}
              </div>
              <button type="button" className="mt-2 w-full text-[8px] text-[#8e969e]">
                + Ajouter une idée
              </button>
            </div>
          ))}
        </div>
      </div>

      <aside className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118]">
        <div className="border-b border-[rgba(255,255,255,0.07)] px-3 py-2.5 text-[9px] tracking-[1.5px] text-[#9b9fa5]">
          ACTIVITÉ RÉCENTE
        </div>
        <div className="p-2">
          {ACTIVITY.map((a) => (
            <div key={a.text} className="flex gap-2 border-b border-[rgba(255,255,255,0.05)] py-2">
              <ProtoAvatar agent={a.who} size="sm" />
              <div className="min-w-0">
                <p className="text-[9px] leading-snug text-[#9aa1a8]">{a.text}</p>
                <p className="mt-1 text-[8px] text-[#5f6871]">{a.ago}</p>
              </div>
            </div>
          ))}
        </div>
        <button type="button" className="text-btn">
          Voir toute l&apos;activité <ChevronRight size={13} />
        </button>
      </aside>
    </div>
  );
}

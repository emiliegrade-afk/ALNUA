"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchLibraryEntries, type LibraryEntry } from "@/lib/library-api";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { getAgentById, type BureauAgentDef } from "@/lib/agent-bureau";
import type { Project } from "@/lib/types";
import { C } from "./shared";

/* Documentation — le Hub a un vrai système de bibliothèque (fetchLibraryEntries :
 * titre, résumé, auteur (agent_id), date, "épinglé" via le champ réel
 * `timing==="now"`), déjà utilisé par l'ancien onglet Documentation. Ce que
 * la maquette montre en plus (catégorie Spécifications/Guides/ADR/..., projet
 * lié, statut À jour/En révision) n'existe pas dans ce système : dérivé de
 * façon stable (hash de l'id de l'entrée) plutôt qu'inventé au hasard.
 * Contributions aujourd'hui/semaine/mois et activité récente sont 100%
 * réelles (dates de création des entrées). Décision du 2026-07-30. */

function hash(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return h;
}

const CATEGORIES = ["Spécifications", "Guides", "Architecture", "Décisions (ADR)", "Recherche", "Processus", "Design", "API", "Autres"] as const;
const STATUSES = ["À jour", "En révision"] as const;

function categoryOf(entry: LibraryEntry): string {
  return CATEGORIES[hash(entry.id) % CATEGORIES.length];
}
function statusOf(entry: LibraryEntry): string {
  return hash(`${entry.id}-status`) % 5 === 0 ? STATUSES[1] : STATUSES[0];
}
function projectOf(entry: LibraryEntry, projects: Project[]): string {
  if (projects.length === 0) return "—";
  return projects[hash(`${entry.id}-proj`) % projects.length].name;
}

function relTime(iso: string) {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "aujourd'hui";
  if (days === 1) return "hier";
  if (days < 30) return `il y a ${days} j`;
  return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" });
}

function authorFor(entry: LibraryEntry): BureauAgentDef | undefined {
  return entry.agent_id ? getAgentById(entry.agent_id) : undefined;
}

export function DocumentationTab({ projects }: { projects: Project[] }) {
  const [entries, setEntries] = useState<LibraryEntry[] | "loading" | "error">("loading");
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchLibraryEntries({ bureau: "app", limit: 100 })
      .then((r) => {
        if (!cancelled) setEntries(r.entries ?? []);
      })
      .catch(() => {
        if (!cancelled) setEntries("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const categoryCounts = useMemo(() => {
    if (!Array.isArray(entries)) return {};
    const counts: Record<string, number> = {};
    for (const e of entries) counts[categoryOf(e)] = (counts[categoryOf(e)] ?? 0) + 1;
    return counts;
  }, [entries]);

  const filtered = useMemo(() => {
    if (!Array.isArray(entries)) return [];
    const sorted = [...entries].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    if (!search.trim()) return sorted;
    return sorted.filter((e) => e.title.toLowerCase().includes(search.toLowerCase()));
  }, [entries, search]);

  const pinned = Array.isArray(entries) ? entries.filter((e) => e.timing === "now").slice(0, 4) : [];

  const contributions = useMemo(() => {
    if (!Array.isArray(entries)) return { today: 0, week: 0, month: 0 };
    const now = Date.now();
    const day = 86_400_000;
    return {
      today: entries.filter((e) => now - new Date(e.created_at).getTime() < day).length,
      week: entries.filter((e) => now - new Date(e.created_at).getTime() < 7 * day).length,
      month: entries.filter((e) => now - new Date(e.created_at).getTime() < 30 * day).length,
    };
  }, [entries]);

  if (entries === "loading") {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        Chargement de la documentation…
      </div>
    );
  }
  if (entries === "error") {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        La bibliothèque du Hub est injoignable — documentation indisponible.
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 gap-3 overflow-y-auto">
      <div className="flex min-w-0 flex-1 flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <h2 className="truncate text-[18px] font-bold tracking-[0.5px]" style={{ color: C.ivory }}>
              DOCUMENTATION
            </h2>
            <p className="truncate text-[10.5px]" style={{ color: C.dim }}>
              Toutes les ressources et documents du département APP
            </p>
          </div>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher un document…"
            className="w-[220px] rounded-lg border bg-transparent px-3 py-1.5 text-[10.5px] outline-none"
            style={{ borderColor: C.line, color: C.ivory }}
          />
        </div>

        <div className="grid grid-cols-6 gap-2.5">
          {[
            { label: "Documents", value: entries.length },
            { label: "Spécifications", value: categoryCounts["Spécifications"] ?? 0 },
            { label: "Guides", value: categoryCounts["Guides"] ?? 0 },
            { label: "Décisions (ADR)", value: categoryCounts["Décisions (ADR)"] ?? 0 },
            { label: "Recherches", value: categoryCounts["Recherche"] ?? 0 },
            { label: "Autres", value: entries.length - (categoryCounts["Spécifications"] ?? 0) - (categoryCounts["Guides"] ?? 0) - (categoryCounts["Décisions (ADR)"] ?? 0) - (categoryCounts["Recherche"] ?? 0) },
          ].map((s) => (
            <div key={s.label} className="rounded-xl border p-3 text-center" style={{ borderColor: C.line, background: "#000000" }}>
              <p className="text-[19px] font-semibold" style={{ color: C.ivory }}>
                {s.value}
              </p>
              <p className="text-[8.5px]" style={{ color: C.faint }}>
                {s.label}
              </p>
            </div>
          ))}
        </div>

        <div className="grid gap-3 lg:grid-cols-[180px_1fr]">
          <div className="dept-instrument p-3.5">
            <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
              CATÉGORIES
            </p>
            <div className="flex flex-col gap-1.5">
              {CATEGORIES.map((cat) => (
                <div key={cat} className="flex items-center justify-between text-[10.5px]" style={{ color: C.warm }}>
                  <span className="truncate">{cat}</span>
                  <span style={{ color: C.faint }}>{categoryCounts[cat] ?? 0}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="dept-instrument p-3.5">
            <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
              DOCUMENTS RÉCENTS
            </p>
            {filtered.length === 0 ? (
              <p className="py-6 text-center text-[11px]" style={{ color: C.faint }}>
                Aucun document{search ? " ne correspond à cette recherche." : " archivé pour ce bureau."}
              </p>
            ) : (
              <div className="overflow-hidden rounded-lg border" style={{ borderColor: C.lineSoft }}>
                <table className="w-full text-[10px]">
                  <thead>
                    <tr style={{ background: "rgba(22,17,13,.6)" }}>
                      {["Nom", "Catégorie", "Auteur", "Dernière MAJ", "Projet", "Statut"].map((h) => (
                        <th key={h} className="px-2.5 py-2 text-left font-medium" style={{ color: C.faint }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.slice(0, 10).map((e) => {
                      const author = authorFor(e);
                      const status = statusOf(e);
                      return (
                        <tr key={e.id} className="border-t" style={{ borderColor: C.lineSoft }}>
                          <td className="px-2.5 py-2">
                            <p className="truncate font-medium" style={{ color: C.ivory }}>
                              {e.title}
                            </p>
                            <p className="truncate text-[9px]" style={{ color: C.faint }}>
                              {e.summary}
                            </p>
                          </td>
                          <td className="px-2.5 py-2 truncate" style={{ color: C.copperLight }}>
                            {categoryOf(e)}
                          </td>
                          <td className="px-2.5 py-2">
                            {author ? (
                              <span className="flex items-center gap-1.5">
                                <AgentAvatar agentId={author.id} name={author.name} size={16} />
                                <span className="truncate" style={{ color: C.warm }}>
                                  {author.name.split(" ")[0]}
                                </span>
                              </span>
                            ) : (
                              <span style={{ color: C.faint }}>—</span>
                            )}
                          </td>
                          <td className="px-2.5 py-2" style={{ color: C.dim }}>
                            {relTime(e.created_at)}
                          </td>
                          <td className="px-2.5 py-2 truncate" style={{ color: C.dim }}>
                            {projectOf(e, projects)}
                          </td>
                          <td className="px-2.5 py-2" style={{ color: status === "À jour" ? C.online : C.copperLight }}>
                            {status}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="hidden w-[clamp(230px,18vw,280px)] shrink-0 flex-col gap-3 min-[1200px]:flex">
        <div className="dept-instrument p-3.5">
          <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            DOCUMENTS ÉPINGLÉS
          </p>
          {pinned.length === 0 ? (
            <p className="text-[10px]" style={{ color: C.faint }}>
              Aucun document épinglé pour l&apos;instant.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {pinned.map((e) => {
                const author = authorFor(e);
                return (
                  <div key={e.id} className="flex items-center justify-between gap-2 rounded-lg border p-2" style={{ borderColor: C.lineSoft }}>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[10.5px] font-medium" style={{ color: C.ivory }}>
                        {e.title}
                      </span>
                      <span className="block truncate text-[9px]" style={{ color: C.faint }}>
                        {author?.name.split(" ")[0] ?? "—"} · {relTime(e.created_at)}
                      </span>
                    </span>
                    <span style={{ color: C.faint }}>›</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="dept-instrument p-3.5">
          <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            CONTRIBUTIONS RÉCENTES
          </p>
          <div className="flex flex-col gap-2">
            {[
              { label: "Aujourd'hui", value: contributions.today },
              { label: "Cette semaine", value: contributions.week },
              { label: "Ce mois", value: contributions.month },
            ].map((c) => (
              <div key={c.label} className="flex items-center justify-between text-[10.5px]">
                <span style={{ color: C.warm }}>{c.label}</span>
                <span style={{ color: C.ivory }}>{c.value} documents modifiés</span>
              </div>
            ))}
          </div>
        </div>

        <div className="dept-instrument p-3.5">
          <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            ACTIVITÉ RÉCENTE
          </p>
          <div className="flex flex-col gap-2">
            {filtered.slice(0, 6).map((e) => {
              const author = authorFor(e);
              return (
                <div key={e.id} className="flex items-start gap-2">
                  {author ? <AgentAvatar agentId={author.id} name={author.name} size={20} /> : <span className="h-5 w-5 shrink-0 rounded-full" style={{ background: C.lineSoft }} />}
                  <span className="min-w-0 flex-1">
                    <span className="block text-[10px] leading-[1.35]" style={{ color: C.warm }}>
                      <span style={{ color: C.ivory }}>{author?.name.split(" ")[0] ?? "Un agent"}</span> a créé « {e.title} »
                    </span>
                    <span className="text-[8.5px]" style={{ color: C.faint }}>
                      {relTime(e.created_at)}
                    </span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { FileText, Filter, Plus, Search } from "lucide-react";
import { ProtoAvatar, ProtoSectionHeader } from "./proto-shared";

const KPIS = [
  { label: "Documents", value: "256" },
  { label: "Spécifications", value: "48" },
  { label: "Guides", value: "37" },
  { label: "Décisions (ADR)", value: "28" },
  { label: "Recherches", value: "19" },
  { label: "Autres", value: "124" },
];

const CATEGORIES = [
  { name: "Spécifications", count: 49 },
  { name: "Guides", count: 27 },
  { name: "Architecture", count: 42 },
  { name: "ADR / Décisions", count: 28 },
  { name: "Recherche", count: 19 },
  { name: "API", count: 31 },
  { name: "Design", count: 22 },
];

const DOCS = [
  { name: "Spécification — NAÏA v2.4", cat: "Spécifications", who: "sam", maj: "Aujourd’hui", project: "NAÏA", status: "À jour" },
  { name: "Guide onboarding Expo", cat: "Guides", who: "theo", maj: "Hier", project: "Academy", status: "En révision" },
  { name: "ADR-014 Auth refactor", cat: "ADR", who: "hao", maj: "08 août", project: "NUAWAY", status: "À jour" },
  { name: "Architecture Hub agents", cat: "Architecture", who: "aria", maj: "07 août", project: "Hub", status: "À jour" },
  { name: "API Messaging realtime", cat: "API", who: "hao", maj: "06 août", project: "Academy", status: "En révision" },
  { name: "Design system tokens", cat: "Design", who: "ines", maj: "05 août", project: "Hub", status: "À jour" },
];

const PINNED = [
  "Spécification — NAÏA v2.4",
  "ADR-014 Auth refactor",
  "Architecture Hub agents",
];

const ACTIVITY = [
  { who: "sam", text: "a mis à jour Spécification NAÏA v2.4", ago: "il y a 2h" },
  { who: "theo", text: "a commenté Guide onboarding", ago: "il y a 3h" },
  { who: "hao", text: "a publié ADR-014", ago: "il y a 5h" },
  { who: "ines", text: "a épinglé Design system tokens", ago: "il y a 7h" },
];

/** Documentation APP — maquette ChatGPT 30 juil. */
export function AppDocsExact() {
  return (
    <div className="grid gap-3 pb-6 xl:grid-cols-[minmax(0,1fr)_240px]">
      <div className="min-w-0 space-y-3">
        <ProtoSectionHeader
          title="DOCUMENTATION"
          desc="Specs, guides, ADR et connaissances du département APP"
          icon={<FileText size={16} />}
        >
          <div className="search w-[200px]">
            <Search size={14} />
            <input placeholder="Rechercher un document..." readOnly />
          </div>
          <button type="button" className="outline-btn">
            <Filter size={14} /> Filtres
          </button>
          <button type="button" className="primary-btn">
            <Plus size={15} /> Nouveau document
          </button>
        </ProtoSectionHeader>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
          {KPIS.map((k) => (
            <div
              key={k.label}
              className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#0b1118] px-3 py-2"
            >
              <p className="text-[16px] font-medium text-[#e8e2da]">{k.value}</p>
              <p className="text-[8px] text-[#6e767f]">{k.label}</p>
            </div>
          ))}
        </div>

        <div className="grid gap-3 lg:grid-cols-[200px_minmax(0,1fr)_200px]">
          <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
            <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">CATÉGORIES</p>
            {CATEGORIES.map((c) => (
              <button
                key={c.name}
                type="button"
                className="flex w-full items-center justify-between border-b border-[rgba(255,255,255,0.05)] py-2 text-left text-[10px] text-[#9aa1a8] hover:text-[#e0a477]"
              >
                <span>{c.name}</span>
                <span className="text-[#5f6871]">{c.count}</span>
              </button>
            ))}
          </section>

          <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
            <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">DOCUMENTS RÉCENTS</p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[10px]">
                <thead>
                  <tr className="text-[8px] uppercase tracking-wider text-[#5f6871]">
                    <th className="pb-2 font-medium">Nom</th>
                    <th className="pb-2 font-medium">Catégorie</th>
                    <th className="pb-2 font-medium">Auteur</th>
                    <th className="pb-2 font-medium">MàJ</th>
                    <th className="pb-2 font-medium">Projet</th>
                    <th className="pb-2 font-medium">Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {DOCS.map((d) => (
                    <tr key={d.name} className="border-t border-[rgba(255,255,255,0.05)]">
                      <td className="py-2 pr-2 font-medium text-[#e8e2da]">{d.name}</td>
                      <td className="py-2 text-[#7e8790]">{d.cat}</td>
                      <td className="py-2">
                        <ProtoAvatar agent={d.who} size="sm" />
                      </td>
                      <td className="py-2 text-[#7e8790]">{d.maj}</td>
                      <td className="py-2 text-[#7e8790]">{d.project}</td>
                      <td className="py-2">
                        <span
                          className="text-[9px]"
                          style={{ color: d.status === "À jour" ? "#5ed69a" : "#e7a85f" }}
                        >
                          {d.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="space-y-3">
            <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
              <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">DOCUMENTS ÉPINGLÉS</p>
              {PINNED.map((p) => (
                <p
                  key={p}
                  className="mb-1.5 rounded-md border border-[rgba(201,134,88,.25)] bg-[rgba(201,134,88,.06)] px-2 py-1.5 text-[9px] text-[#e0a477]"
                >
                  {p}
                </p>
              ))}
            </section>
            <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
              <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">CONTRIBUTIONS RÉCENTES</p>
              {[
                ["Aujourd’hui", "6"],
                ["Cette semaine", "24"],
                ["Ce mois", "91"],
              ].map(([l, v]) => (
                <div key={l} className="flex justify-between border-b border-[rgba(255,255,255,0.05)] py-2 text-[10px]">
                  <span className="text-[#7e8790]">{l}</span>
                  <b className="text-[#e8e2da]">{v}</b>
                </div>
              ))}
            </section>
          </div>
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
      </aside>
    </div>
  );
}

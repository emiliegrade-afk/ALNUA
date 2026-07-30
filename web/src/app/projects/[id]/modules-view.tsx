"use client";

import { useState } from "react";
import { updateModule } from "@/lib/modules";
import { CreateModuleModal } from "@/components/shared/create-module-modal";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { ModuleStatus, Project, ProjectModule } from "@/lib/types";
import { C } from "../../app-v2/shared";
import { featuresForModule, dependenciesForModule } from "./mock-data";

/* Modules — table réelle `project_modules` depuis la Phase 14 (ROADMAP.md,
 * 2026-07-30) : nom/statut/progression/fonctionnalités/tests/bugs viennent de
 * Supabase. `featuresForModule`/`dependenciesForModule` (le détail ligne par
 * ligne d'un module — sous-fonctionnalités et dépendances) restent provisoires
 * (mock-data.ts) : il n'existe pas encore de table pour ce niveau de détail. */

const MODULE_TABS = ["Fonctionnalités", "Missions", "Équipe", "Documentation", "Analytics"] as const;

const STATUS_LABEL: Record<ModuleStatus, string> = {
  a_faire: "À faire",
  en_developpement: "En développement",
  en_test: "En test",
  termine: "Terminé",
};

const STATUS_COLOR: Record<ModuleStatus, string> = {
  a_faire: C.faint,
  en_developpement: C.copperLight,
  en_test: "#E0A95C",
  termine: C.online,
};

function ModuleCard({ module, onOpen }: { module: ProjectModule; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex flex-col gap-2.5 rounded-xl border p-3.5 text-left"
      style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-[13px] font-semibold" style={{ color: C.ivory }}>
          {module.name}
        </span>
        <span
          className="shrink-0 rounded-full border px-2 py-0.5 text-[8.5px]"
          style={{ borderColor: "rgba(200,127,78,.25)", color: STATUS_COLOR[module.status] }}
        >
          {STATUS_LABEL[module.status]}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(200,127,78,.15)" }}>
          <span
            className="block h-full rounded-full"
            style={{ width: `${module.progress}%`, background: `linear-gradient(90deg,#8A5230,${C.copperLight})` }}
          />
        </span>
        <span className="text-[11px] font-semibold" style={{ color: C.ivory }}>
          {module.progress}%
        </span>
      </div>
      <div className="flex items-center gap-3 text-[9.5px]" style={{ color: C.faint }}>
        <span>
          {module.features_done}/{module.features_total} fonctionnalités
        </span>
        <span>{module.tests_passed_pct}% tests</span>
        <span>{module.open_bugs} bugs</span>
      </div>
    </button>
  );
}

function ModuleDetail({
  module,
  projectName,
  agents,
  onBack,
  onModuleUpdated,
}: {
  module: ProjectModule;
  projectName: string;
  agents: BureauAgentDef[];
  onBack: () => void;
  onModuleUpdated: (m: ProjectModule) => void;
}) {
  const [tab, setTab] = useState<(typeof MODULE_TABS)[number]>("Fonctionnalités");
  const [savingStatus, setSavingStatus] = useState(false);
  const features = featuresForModule(module.id, agents.map((a) => a.name));
  const deps = dependenciesForModule(module.id);

  async function handleStatusChange(next: ModuleStatus) {
    setSavingStatus(true);
    try {
      const updated = await updateModule(module.id, { status: next });
      onModuleUpdated(updated);
    } catch {
      // dégradé silencieux — l'utilisateur peut réessayer
    } finally {
      setSavingStatus(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <button
        type="button"
        onClick={onBack}
        className="flex w-fit items-center gap-1.5 text-[11px]"
        style={{ color: C.warm }}
      >
        ← Retour aux modules
      </button>

      <div className="flex items-center gap-4">
        <span
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border text-[18px]"
          style={{ borderColor: "rgba(200,127,78,.4)", color: C.copperLight, background: "rgba(200,127,78,.1)" }}
        >
          ◈
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-[19px] font-bold" style={{ color: C.ivory }}>
            {module.name}
          </h2>
          <p className="text-[10.5px]" style={{ color: C.faint }}>
            Module • {projectName}
          </p>
        </div>
        <div className="relative h-[52px] w-[52px] shrink-0">
          <svg width="52" height="52" viewBox="0 0 52 52">
            <circle cx="26" cy="26" r="21" fill="none" stroke="rgba(200,127,78,.15)" strokeWidth="4.5" />
            <circle
              cx="26"
              cy="26"
              r="21"
              fill="none"
              stroke={C.copper}
              strokeWidth="4.5"
              strokeLinecap="round"
              strokeDasharray={`${((module.progress / 100) * 2 * Math.PI * 21).toFixed(1)} ${(2 * Math.PI * 21).toFixed(1)}`}
              transform="rotate(-90 26 26)"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[12px] font-semibold">
            {module.progress}%
          </span>
        </div>
        <select
          value={module.status}
          onChange={(e) => void handleStatusChange(e.target.value as ModuleStatus)}
          disabled={savingStatus}
          className="shrink-0 rounded-full border bg-transparent px-2.5 py-1 text-[9.5px] outline-none"
          style={{ borderColor: "rgba(200,127,78,.3)", color: STATUS_COLOR[module.status] }}
        >
          {(Object.keys(STATUS_LABEL) as ModuleStatus[]).map((s) => (
            <option key={s} value={s} style={{ color: "#000" }}>
              {STATUS_LABEL[s]}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Fonctionnalités", value: `${module.features_done} / ${module.features_total}` },
          { label: "Tests passés", value: `${module.tests_passed_pct}%` },
          { label: "Bugs ouverts", value: String(module.open_bugs) },
        ].map((s) => (
          <div key={s.label} className="rounded-xl border p-3 text-center" style={{ borderColor: C.line, background: "rgba(22,17,13,.5)" }}>
            <p className="text-[17px] font-semibold" style={{ color: C.ivory }}>
              {s.value}
            </p>
            <p className="text-[8.5px]" style={{ color: C.faint }}>
              {s.label}
            </p>
          </div>
        ))}
      </div>

      <div className="flex gap-4 border-b" style={{ borderColor: C.lineSoft }}>
        {MODULE_TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className="border-b-2 pb-2 text-[10.5px]"
            style={{ borderColor: tab === t ? C.copper : "transparent", color: tab === t ? "#F2E9DE" : C.faint }}
          >
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="flex flex-col gap-4">
          {tab === "Fonctionnalités" ? (
            <div className="overflow-hidden rounded-xl border" style={{ borderColor: C.line }}>
              <table className="w-full text-[10.5px]">
                <thead>
                  <tr style={{ background: "rgba(22,17,13,.6)" }}>
                    {["Fonctionnalité", "Statut", "Responsable", "Progression"].map((h) => (
                      <th key={h} className="px-3 py-2 text-left font-medium" style={{ color: C.faint }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {features.map((f) => (
                    <tr key={f.name} className="border-t" style={{ borderColor: C.lineSoft }}>
                      <td className="px-3 py-2" style={{ color: C.ivory }}>
                        {f.name}
                      </td>
                      <td className="px-3 py-2" style={{ color: f.status === "Terminé" ? C.online : C.warm }}>
                        {f.status}
                      </td>
                      <td className="px-3 py-2 truncate" style={{ color: C.dim }}>
                        {f.responsible}
                      </td>
                      <td className="px-3 py-2" style={{ color: C.ivory }}>
                        {f.progress}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div
              className="flex min-h-[160px] items-center justify-center rounded-xl border text-[11px]"
              style={{ borderColor: C.line, color: C.faint }}
            >
              {tab} — à venir.
            </div>
          )}

          <div className="rounded-xl border p-3.5" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
            <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
              DÉPENDANCES
            </p>
            <div className="flex flex-wrap gap-2">
              {deps.map((d) => (
                <span
                  key={d.label}
                  className="flex flex-col rounded-lg border px-3 py-1.5 text-[10px]"
                  style={{ borderColor: C.lineSoft }}
                >
                  <span style={{ color: C.warm }}>{d.label}</span>
                  <span style={{ color: d.status === "Terminé" ? C.online : C.copperLight }}>{d.status}</span>
                </span>
              ))}
            </div>
          </div>
        </div>

        <div
          className="flex flex-col items-center gap-3 rounded-xl border p-4"
          style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
        >
          <p className="w-full text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            APERÇU RAPIDE
          </p>
          <div
            className="flex h-[220px] w-[120px] flex-col items-center justify-center gap-1 rounded-[18px] border-4 p-2"
            style={{ borderColor: "#2A231C", background: "#0C0A08" }}
          >
            <span className="text-[9px]" style={{ color: C.faint }}>
              Aujourd&apos;hui
            </span>
            <span className="text-[24px] font-semibold" style={{ color: C.ivory }}>
              {module.features_done * 20}
            </span>
            <span className="text-[8px]" style={{ color: C.faint }}>
              unités
            </span>
          </div>
          <p className="text-center text-[9px]" style={{ color: C.faint }}>
            Aperçu illustratif — pas de rendu mobile réel branché.
          </p>
        </div>
      </div>
    </div>
  );
}

export function ModulesView({
  project,
  agents,
  modules,
  loading,
  onModulesChange,
}: {
  project: Project;
  agents: BureauAgentDef[];
  modules: ProjectModule[];
  loading: boolean;
  onModulesChange: (modules: ProjectModule[]) => void;
}) {
  const [openId, setOpenId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const active = modules.find((m) => m.id === openId) ?? null;

  if (loading) {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        Chargement des modules…
      </div>
    );
  }

  if (active) {
    return (
      <ModuleDetail
        module={active}
        projectName={project.name}
        agents={agents}
        onBack={() => setOpenId(null)}
        onModuleUpdated={(updated) => onModulesChange(modules.map((m) => (m.id === updated.id ? updated : m)))}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          MODULES DU PROJET
        </p>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="rounded-[18px] border px-3.5 py-1.5 text-[11px]"
          style={{ borderColor: "rgba(200,127,78,.45)", background: "rgba(200,127,78,.12)", color: C.copperLight }}
        >
          ＋ Nouveau module
        </button>
      </div>

      {modules.length === 0 ? (
        <div className="flex min-h-[180px] items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          Aucun module pour ce projet pour le moment.
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(230px,1fr))] gap-3">
          {modules.map((m) => (
            <ModuleCard key={m.id} module={m} onOpen={() => setOpenId(m.id)} />
          ))}
        </div>
      )}

      <CreateModuleModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        projectId={project.id}
        onCreated={(m) => onModulesChange([...modules, m])}
      />
    </div>
  );
}

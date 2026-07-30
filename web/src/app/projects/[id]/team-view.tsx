"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { getAgentById, type BureauAgentDef } from "@/lib/agent-bureau";
import { HUB_CHIEF } from "@/lib/console/owner";
import { ROUTES } from "@/lib/routes";
import type { Project } from "@/lib/types";
import type { AgentStatus } from "@/lib/openroom-api";
import { C, STATUS_COLOR, STATUS_TEXT } from "../../app-v2/shared";
import { agentStats } from "./mock-data";
import { ConversationView } from "./conversation-view";

/* Onglet Équipe du détail projet : liste + bascule "Flow" (graphe des
   connexions), drill-down vers la fiche agent (Panel 2), qui ouvre elle-même
   la conversation (Panel 5). */

function AgentFiche({
  agent,
  status,
  onBack,
  onOpenChat,
}: {
  agent: BureauAgentDef;
  status?: AgentStatus;
  onBack: () => void;
  onOpenChat: () => void;
}) {
  const [tab, setTab] = useState<"Aperçu" | "Missions" | "Activité" | "Compétences" | "Documents" | "Mémoire" | "Paramètres">(
    "Aperçu",
  );
  const stats = useMemo(() => agentStats(agent.id, agent.skills), [agent.id, agent.skills]);
  const online = status?.status === "working" || status?.status === "waiting";

  return (
    <div className="flex flex-col gap-4">
      <button type="button" onClick={onBack} className="flex w-fit items-center gap-1.5 text-[11px]" style={{ color: C.warm }}>
        ← Retour à l&apos;équipe
      </button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <AgentAvatar agentId={agent.id} name={agent.name} size={64} ring />
          <div>
            <div className="flex items-center gap-1.5">
              <h2 className="text-[20px] font-bold" style={{ color: C.ivory }}>
                {agent.name}
              </h2>
              <span style={{ color: C.copperLight }}>✔</span>
            </div>
            <p className="text-[12px]" style={{ color: C.muted }}>
              {agent.role}
            </p>
            <p className="mt-1 flex items-center gap-1.5 text-[10px]" style={{ color: online ? C.online : C.faint }}>
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: online ? C.online : C.faint }} />
              {online ? "En activité" : "En veille"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenChat}
            className="rounded-[18px] border px-4 py-1.5 text-[11px]"
            style={{ borderColor: "rgba(200,127,78,.45)", background: "rgba(200,127,78,.12)", color: C.copperLight }}
          >
            Discuter
          </button>
          <Link
            href={`${ROUTES.openroom}?agent=${encodeURIComponent(agent.id)}`}
            className="rounded-[18px] border px-4 py-1.5 text-[11px]"
            style={{ borderColor: C.line, color: C.warm }}
          >
            Assigner une tâche
          </Link>
        </div>

        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-[10.5px]" style={{ color: C.faint }}>
          <span>
            Disponibilité <b style={{ color: C.ivory }}>{stats.availability}%</b>
          </span>
          <span>
            Charge actuelle <b style={{ color: C.ivory }}>{stats.currentLoad}%</b>
          </span>
          <span>
            Depuis <b style={{ color: C.ivory }}>{Math.floor(stats.tenureMonths / 12)} ans {stats.tenureMonths % 12} mois</b>
          </span>
          <span>
            Localisation <b style={{ color: C.ivory }}>{stats.location}</b>
          </span>
          <span>
            Langues <b style={{ color: C.ivory }}>{stats.languages}</b>
          </span>
        </div>
      </div>

      <div className="flex gap-4 overflow-x-auto border-b" style={{ borderColor: C.lineSoft }}>
        {(["Aperçu", "Missions", "Activité", "Compétences", "Documents", "Mémoire", "Paramètres"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className="shrink-0 whitespace-nowrap border-b-2 pb-2 text-[10.5px]"
            style={{ borderColor: tab === t ? C.copper : "transparent", color: tab === t ? "#F2E9DE" : C.faint }}
          >
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      {tab === "Aperçu" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="flex flex-col gap-4">
            <section className="rounded-xl border p-4" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
              <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
                MISSION EN COURS
              </p>
              <p className="text-[12px] font-semibold">{status?.currentTask ?? "Aucune mission en cours."}</p>
              {status?.progress != null ? (
                <div className="mt-2 flex items-center gap-2">
                  <span className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(200,127,78,.15)" }}>
                    <span className="block h-full rounded-full" style={{ width: `${status.progress}%`, background: C.copper }} />
                  </span>
                  <span className="text-[11px] font-semibold">{status.progress}%</span>
                </div>
              ) : null}
            </section>

            <section className="rounded-xl border p-4" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
              <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
                COMPÉTENCES
              </p>
              <div className="flex flex-col gap-2">
                {stats.skills.map((s) => (
                  <div key={s.label} className="flex items-center gap-2">
                    <span className="w-[110px] shrink-0 truncate text-[10px]" style={{ color: C.warm }}>
                      {s.label}
                    </span>
                    <span className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(200,127,78,.15)" }}>
                      <span
                        className="block h-full rounded-full"
                        style={{ width: `${s.value}%`, background: `linear-gradient(90deg,#8A5230,${C.copperLight})` }}
                      />
                    </span>
                    <span className="w-8 shrink-0 text-right text-[10px]" style={{ color: C.ivory }}>
                      {s.value}%
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="flex flex-col gap-4">
            <section className="rounded-xl border p-4" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
              <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
                ACTIVITÉ RÉCENTE
              </p>
              <div className="flex flex-col gap-1.5">
                {(status?.log ?? []).slice(-5).map((l, i) => (
                  <p key={i} className="truncate text-[10.5px]" style={{ color: C.muted }}>
                    {l}
                  </p>
                ))}
                {(status?.log ?? []).length === 0 ? (
                  <p className="text-[10.5px]" style={{ color: C.faint }}>
                    Aucune activité récente.
                  </p>
                ) : null}
              </div>
            </section>

            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Missions terminées", value: `${stats.missionsDone}` },
                { label: "Qualité du code", value: `${stats.codeQuality}%` },
                { label: "Respect délais", value: `${stats.onTime}%` },
                { label: "Collaboration", value: `${stats.collaboration}%` },
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
          </div>
        </div>
      ) : (
        <div
          className="flex min-h-[200px] items-center justify-center rounded-xl border text-[11px]"
          style={{ borderColor: C.line, background: "rgba(16,13,11,.55)", color: C.faint }}
        >
          {tab} — à venir.
        </div>
      )}
    </div>
  );
}

function ProjectFlow({ agents, selectedId, onSelect }: { agents: BureauAgentDef[]; selectedId: string; onSelect: (id: string) => void }) {
  const selected = agents.find((a) => a.id === selectedId) ?? agents[0];
  const others = agents.filter((a) => a.id !== selected?.id);
  const nodes = [...others, { id: "coo", name: HUB_CHIEF.name, role: "COO", skills: [] } as unknown as BureauAgentDef, { id: "store", name: "Store", role: "Publication", skills: [] } as unknown as BureauAgentDef];
  const R = 165;
  const cx = 320;
  const cy = 230;

  return (
    <div
      className="relative h-[520px] overflow-hidden rounded-xl border"
      style={{ borderColor: C.line, background: "radial-gradient(circle at 50% 50%, rgba(200,127,78,.05), rgba(16,13,11,.6))" }}
    >
      <svg className="absolute inset-0 h-full w-full" style={{ pointerEvents: "none" }}>
        {nodes.map((_, i) => {
          const angle = (i / nodes.length) * 2 * Math.PI - Math.PI / 2;
          const x = cx + R * Math.cos(angle);
          const y = cy + R * Math.sin(angle);
          return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(200,127,78,.25)" strokeWidth={1.5} />;
        })}
      </svg>

      <button
        type="button"
        onClick={() => selected && onSelect(selected.id)}
        className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1"
        style={{ left: cx, top: cy }}
      >
        <AgentAvatar agentId={selected?.id ?? ""} name={selected?.name ?? ""} size={56} ring />
        <span className="rounded-lg border px-2 py-1 text-center text-[10px]" style={{ borderColor: C.lineStrong, background: "rgba(16,13,11,.85)", color: C.ivory }}>
          {selected?.name}
          <br />
          <span style={{ color: C.faint }}>{selected?.role}</span>
        </span>
      </button>

      {nodes.map((n, i) => {
        const angle = (i / nodes.length) * 2 * Math.PI - Math.PI / 2;
        const x = cx + R * Math.cos(angle);
        const y = cy + R * Math.sin(angle);
        const clickable = n.id !== "coo" && n.id !== "store";
        return (
          <button
            key={n.id}
            type="button"
            disabled={!clickable}
            onClick={() => clickable && onSelect(n.id)}
            className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1"
            style={{ left: x, top: y }}
          >
            {n.id === "store" ? (
              <span className="flex h-10 w-10 items-center justify-center rounded-full border text-[16px]" style={{ borderColor: C.lineStrong, color: C.copperLight }}>
                ⬒
              </span>
            ) : (
              <AgentAvatar agentId={n.id} name={n.name} size={40} />
            )}
            <span className="rounded-lg border px-1.5 py-0.5 text-center text-[9px]" style={{ borderColor: C.lineSoft, background: "rgba(16,13,11,.85)", color: C.warm }}>
              {n.name}
              <br />
              <span style={{ color: C.faint }}>{n.role}</span>
            </span>
          </button>
        );
      })}

      <div className="absolute bottom-3 left-3 flex gap-3 text-[9px]" style={{ color: C.faint }}>
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: C.online }} /> En activité
        </span>
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: C.faint }} /> En veille
        </span>
      </div>
    </div>
  );
}

export function TeamView({
  project,
  agents,
  statuses,
}: {
  project: Project;
  agents: BureauAgentDef[];
  statuses: Record<string, AgentStatus>;
}) {
  const [view, setView] = useState<"list" | "flow">("list");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);

  const selected = selectedId ? getAgentById(selectedId) : undefined;

  if (selected && chatOpen) {
    return <ConversationView agents={agents} initialAgentId={selected.id} onBack={() => setChatOpen(false)} />;
  }
  if (selected) {
    return (
      <AgentFiche
        agent={selected}
        status={statuses[selected.id]}
        onBack={() => setSelectedId(null)}
        onOpenChat={() => setChatOpen(true)}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          ÉQUIPE — {project.name}
        </p>
        <span className="flex overflow-hidden rounded-lg border" style={{ borderColor: C.line }}>
          {(["list", "flow"] as const).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setView(v)}
              className="px-3 py-1 text-[10px]"
              style={{ background: view === v ? "rgba(200,127,78,.18)" : "transparent", color: view === v ? C.copperLight : C.faint }}
            >
              {v === "list" ? "Liste" : "Flow"}
            </button>
          ))}
        </span>
      </div>

      {view === "flow" ? (
        <ProjectFlow agents={agents} selectedId={selectedId ?? agents[0]?.id ?? ""} onSelect={setSelectedId} />
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
          {agents.map((a) => {
            const s = statuses[a.id];
            const online = s?.status === "working" || s?.status === "waiting";
            return (
              <button
                key={a.id}
                type="button"
                onClick={() => setSelectedId(a.id)}
                className="flex items-center gap-2.5 rounded-xl border p-3 text-left"
                style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
              >
                <AgentAvatar agentId={a.id} name={a.name} size={40} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[12px] font-semibold">{a.name}</span>
                  <span className="block truncate text-[9.5px]" style={{ color: C.faint }}>
                    {a.role}
                  </span>
                </span>
                <span
                  className="h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{ background: online ? STATUS_COLOR[s?.status ?? "idle"] : C.faint }}
                  title={STATUS_TEXT[s?.status ?? "idle"]}
                />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

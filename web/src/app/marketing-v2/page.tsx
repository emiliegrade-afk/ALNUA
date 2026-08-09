"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { MarketingConsole } from "@/components/marketing/marketing-console";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData, ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { ROUTES } from "@/lib/routes";
import type { TicketWithProject } from "@/lib/tickets";
import type { Project } from "@/lib/types";
import { C, STATUS_LOAD, STATUS_TEXT, STATUS_COLOR, KIND_META } from "../app-v2/shared";
import { MissionBox, ChatPanel, RecentTasksPanel, ApercuPanel } from "../app-v2/team";
import { useCooStore } from "@/store/coo-store";
import { CooDrawer } from "@/components/shared/coo-drawer";
import { VueGlobaleTab } from "./vue-globale-tab";
import { ContentStudioTab } from "./content-studio-tab";
import { CampagnesTab } from "./campagnes-tab";
import { SocialMediaTab } from "./social-media-tab";
import { AnalyticsTab } from "./analytics-tab";
import { AutomatisationTab } from "./automatisation-tab";
import { ComingSoonTab } from "./coming-soon-tab";

/* ────────────────────────────────────────────────────────────────────────────
   Département Marketing v2 — Phase 29, ROADMAP.md ("Marketing Command
   Center"). Même socle que /app-v2, /gaming-v2, /rnd-v2, /finances-v2.
   Contrairement à Finances (déjà riche en données), Marketing n'avait ni
   dashboard chiffré ni client API dédié avant cette phase — la Vue globale
   n'affiche que des données réelles (file posts_queue, leaderboard de
   compétition, dépenses catégorie "marketing") : aucune métrique Reach/ROI/
   Audience, qui n'existent nulle part dans le code (table campaigns/
   intégration Ads réelle prévues Phase 33). /marketing reste la route
   legacy (DepartmentWorkspace générique), inchangée en parallèle ; cette
   route n'est pas encore liée à la nav principale (CONSOLE_POLES pointe
   toujours vers /marketing), accessible en URL directe.
   ──────────────────────────────────────────────────────────────────────────── */

const TABS = [
  "Équipe",
  "Vue globale",
  "Campagnes",
  "Content Studio",
  "Social Media",
  "Analytics",
  "Automatisation",
  "SEO",
  "Brand Center",
] as const;
type Tab = (typeof TABS)[number];

const TAB_ICON: Record<Tab, string> = {
  Équipe: "👥",
  "Vue globale": "◉",
  "Content Studio": "📝",
  Campagnes: "📣",
  "Social Media": "📱",
  Analytics: "📊",
  Automatisation: "⚙",
  SEO: "🔎",
  "Brand Center": "🎨",
};

const QUICK_ACTIONS = [
  { icon: "＋", label: "Instruction Marketing" },
  { icon: "▤", label: "Rapport d'équipe" },
  { icon: "◎", label: "Analyse de contenu" },
  { icon: "⚙", label: "Automatisation" },
] as const;

function MarketingDepartmentView() {
  const agents = getAgentsForBureau("marketing");
  const statuses = useAgentStatuses();
  const { activityFeed, stats } = useConsoleData();
  const [tab, setTab] = useState<Tab>("Équipe");
  const [selectedId, setSelectedId] = useState(agents[0]?.id ?? "");

  const openDrawer = useCooStore((s) => s.openDrawer);
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);

  function requestNewAgent() {
    setPrefillMessage(
      "Je veux ajouter un agent au pôle Marketing. Quel rôle manque-t-il et comment le créer ? ",
    );
    openDrawer();
  }

  function requestMarketingInstruction() {
    setPrefillMessage("Je veux transmettre une instruction marketing à l'équipe. Sujet : ");
    openDrawer();
  }

  const selected: BureauAgentDef | undefined = agents.find((a) => a.id === selectedId) ?? agents[0];
  const selStatus = selected ? statuses[selected.id]?.status ?? "idle" : "idle";
  const selLoad = STATUS_LOAD[selStatus];

  const activeCount = agents.filter((a) => {
    const s = statuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;

  const agentTasks = useMemo(
    () => (selected ? activityFeed.filter((e) => e.agent === selected.name).slice(0, 6) : []),
    [activityFeed, selected],
  );

  // Pas de registre de "projets" propre au bureau Marketing (comme
  // /marketing legacy, projectBranch: null) — tableaux honnêtement vides
  // plutôt qu'un filtre sur une branche qui n'existe pas pour ce bureau.
  const projects: Project[] = [];
  const tickets: TicketWithProject[] = [];

  if (!selected) {
    return (
      <p className="p-8 text-sm" style={{ color: C.dim }}>
        Aucun agent dans le bureau Marketing.
      </p>
    );
  }

  return (
    <DeptV2PageShell deptHref={ROUTES.marketing} activeDeptId="marketing" coreSubtitle="Hub opérationnel">
        <div className="flex min-w-0 flex-1 flex-col gap-3 px-4 pb-3 pt-3.5">
          <div className="flex shrink-0 items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] border text-[15px]"
                style={{ borderColor: "rgba(192,138,114,.4)", background: "radial-gradient(circle at 30% 20%, rgba(192,138,114,.25), rgba(14,16,20,.9))", color: C.copperLight }}
              >
                📣
              </span>
              <div className="flex min-w-0 items-baseline gap-3">
                <h1 className="truncate text-[22px] leading-[1.1] tracking-[.3px]">
                  <span className="font-bold">MARKETING</span>{" "}
                  <span className="font-light tracking-[4px]" style={{ color: "#A7ADB5" }}>
                    COMMAND CENTER
                  </span>
                </h1>
                <p className="hidden shrink-0 truncate text-[12px] sm:block" style={{ color: C.dim }}>
                  Contenu · Campagnes · Réseaux sociaux
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-[9px]">
              <span
                className="hidden items-center gap-[7px] rounded-[18px] border px-[13px] py-1.5 text-[11.5px] sm:flex"
                style={{ borderColor: "rgba(192,138,114,.22)", background: "rgba(19,22,27,.6)", color: C.warm }}
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: C.online, boxShadow: `0 0 6px ${C.online}` }} />
                {activeCount} agent{activeCount !== 1 ? "s" : ""} actif{activeCount !== 1 ? "s" : ""}
              </span>
              <button
                type="button"
                onClick={requestNewAgent}
                className="flex items-center gap-1.5 rounded-[18px] border px-[13px] py-1.5 text-[11.5px]"
                style={{ borderColor: "rgba(192,138,114,.45)", background: "rgba(192,138,114,.08)", color: C.copperLight }}
              >
                ＋ <span className="hidden sm:inline">Ajouter un agent</span>
              </button>
            </div>
          </div>

          <div className="flex gap-5 overflow-x-auto border-b" style={{ borderColor: "rgba(192,138,114,.15)" }}>
            {TABS.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className="flex shrink-0 items-center gap-[7px] whitespace-nowrap border-b-2 pb-2 pt-1 text-[10.5px] tracking-[1.2px]"
                style={{ borderColor: tab === t ? C.copper : "transparent", color: tab === t ? "#F5F2EA" : C.faint }}
              >
                <span className="text-[11px]">{TAB_ICON[t]}</span>
                {t.toUpperCase()}
              </button>
            ))}
          </div>

          <div className="flex min-h-0 flex-1 flex-col">
            {tab === "Équipe" ? (
              <EquipeTab
                agents={agents}
                statuses={statuses}
                selected={selected}
                selectedId={selectedId}
                setSelectedId={setSelectedId}
                selStatus={selStatus}
                selLoad={selLoad}
                activeCount={activeCount}
                tickets={tickets}
                projects={projects}
                agentTasks={agentTasks}
                activityFeed={activityFeed}
              />
            ) : tab === "Vue globale" ? (
              <VueGlobaleTab onOpenCampagnes={() => setTab("Campagnes")} />
            ) : tab === "Content Studio" ? (
              <ContentStudioTab />
            ) : tab === "Campagnes" ? (
              <CampagnesTab />
            ) : tab === "Social Media" ? (
              <SocialMediaTab />
            ) : tab === "Analytics" ? (
              <AnalyticsTab />
            ) : tab === "Automatisation" ? (
              <AutomatisationTab />
            ) : tab === "SEO" ? (
              <ComingSoonTab
                title="SEO"
                reason="Aucun outil de suivi mots-clés/positionnement n'est branché au Hub aujourd'hui (pas d'intégration Google Search Console, Ahrefs ou équivalent)."
              />
            ) : (
              <ComingSoonTab
                title="Brand Center"
                reason="Le Brand Design transversal (validation de cohérence de marque) n'est pas encore construit — Phase 35, ROADMAP.md, non démarrée."
              />
            )}
          </div>

          {/* ══ COMMAND BAR ══ */}
          <div className="relative flex h-[clamp(54px,7vh,62px)] shrink-0 items-center">
            <span
              className="absolute inset-0 rounded-[34px] border"
              style={{ borderColor: "rgba(192,138,114,.28)", background: "radial-gradient(60% 220% at 50% 50%, rgba(192,138,114,.14), rgba(14,11,9,.7) 70%)" }}
            />
            <div className="relative flex flex-1 items-center justify-between px-7">
              <span className="hidden text-[12px] sm:inline" style={{ color: C.muted }}>
                Que souhaitez-vous faire aujourd&apos;hui ?
              </span>
              <div className="ml-auto flex items-center gap-3 text-[11.5px]" style={{ color: C.warm }}>
                {QUICK_ACTIONS.map((qa) =>
                  qa.label === "Instruction Marketing" ? (
                    // Seule action réellement câblée du groupe (label toujours
                    // visible, fond distinct — précédent rnd-v2, signalé par
                    // Emilie : boutons introuvables sous ~1280px si le libellé
                    // se masque comme les icônes décoratives).
                    <button
                      key={qa.label}
                      type="button"
                      onClick={requestMarketingInstruction}
                      title={qa.label}
                      className="flex items-center gap-[7px] rounded-full border px-2.5 py-1"
                      style={{ borderColor: "rgba(192,138,114,.4)", background: "rgba(192,138,114,.1)" }}
                    >
                      <span className="flex h-[22px] w-[22px] items-center justify-center rounded-md border text-[10px]" style={{ borderColor: "rgba(192,138,114,.28)", color: C.copperLight }}>
                        {qa.icon}
                      </span>
                      <span style={{ color: C.copperLight }}>{qa.label}</span>
                    </button>
                  ) : (
                    <span key={qa.label} title={qa.label} className="flex items-center gap-[7px]">
                      <span className="flex h-[22px] w-[22px] items-center justify-center rounded-md border text-[10px]" style={{ borderColor: "rgba(192,138,114,.28)", color: C.copperLight }}>
                        {qa.icon}
                      </span>
                      <span className="hidden xl:inline">{qa.label}</span>
                    </span>
                  ),
                )}
              </div>
            </div>
            <span
              className="absolute left-1/2 top-1/2 flex h-[88px] w-[88px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full"
              style={{ background: "radial-gradient(circle, rgba(192,138,114,.30) 0%, rgba(192,138,114,.10) 45%, transparent 70%)" }}
            >
              <span className="absolute h-[76px] w-[76px] rounded-full border" style={{ borderColor: "rgba(192,138,114,.35)" }} />
              <AlnuaStar size={60} glow sparkMid="#D9A88F" sparkOuter="#C08A72" glowColorRgb="192,138,114" />
            </span>
          </div>

          {/* Console Marketing — repliée par défaut, fonctionnalité réelle de
              l'ancien /marketing, préservée mais pas visible sans défiler
              volontairement (même pattern que gaming-v2). */}
          <details className="group shrink-0 rounded-xl border" style={{ borderColor: C.line }}>
            <summary className="flex cursor-pointer items-center gap-2 px-4 py-2.5 text-[10.5px]" style={{ color: C.dim }}>
              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
              Console Marketing — instructions directes
            </summary>
            <div className="alnua-scroll max-h-[46vh] overflow-y-auto border-t p-4" style={{ borderColor: C.line }}>
              <MarketingConsole />
            </div>
          </details>
        </div>
    </DeptV2PageShell>
  );
}

function EquipeTab({
  agents,
  statuses,
  selected,
  selectedId,
  setSelectedId,
  selStatus,
  selLoad,
  activeCount,
  tickets,
  projects,
  agentTasks,
  activityFeed,
}: {
  agents: BureauAgentDef[];
  statuses: ReturnType<typeof useAgentStatuses>;
  selected: BureauAgentDef;
  selectedId: string;
  setSelectedId: (id: string) => void;
  selStatus: ReturnType<typeof useAgentStatuses>[string]["status"];
  selLoad: number;
  activeCount: number;
  tickets: TicketWithProject[];
  projects: Project[];
  agentTasks: ReturnType<typeof useConsoleData>["activityFeed"];
  activityFeed: ReturnType<typeof useConsoleData>["activityFeed"];
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <div className="flex shrink-0 gap-3">
        {/* Roster — 7 agents réels, ligne scrollable horizontalement plutôt
            qu'une grille qui empile plusieurs rangées (même pattern que
            gaming-v2). Pas de grille de stats fabriquées (Marketing n'a pas
            d'équivalent build/FPS) — juste avatar/rôle/statut/charge. */}
        <div className="alnua-scroll flex min-w-0 flex-1 gap-3 overflow-x-auto pb-1">
          {agents.map((agent) => {
            const s = statuses[agent.id]?.status ?? "idle";
            const load = STATUS_LOAD[s];
            const active = agent.id === selectedId;
            return (
              <button
                key={agent.id}
                type="button"
                onClick={() => setSelectedId(agent.id)}
                className="flex w-[210px] shrink-0 flex-col gap-2.5 rounded-xl border p-3 text-left transition-colors"
                style={{
                  borderColor: active ? C.copper : C.line,
                  background: active
                    ? "radial-gradient(120% 120% at 0% 0%, rgba(192,138,114,.12), rgba(19,22,27,.6) 60%)"
                    : "rgba(19,22,27,.55)",
                  boxShadow: active ? "0 0 22px rgba(192,138,114,.12)" : undefined,
                }}
              >
                <div className="flex items-center gap-2.5">
                  <AgentAvatar agentId={agent.id} name={agent.name} size={40} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[12.5px] font-semibold">{agent.name}</span>
                    <span className="block truncate text-[9.5px]" style={{ color: C.dim }}>
                      {agent.role}
                    </span>
                  </span>
                  <span className="h-[6px] w-[6px] shrink-0 rounded-full" style={{ background: STATUS_COLOR[s] }} title={STATUS_TEXT[s]} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-1 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(192,138,114,.15)" }}>
                    <span className="block h-full rounded-full" style={{ width: `${load}%`, background: C.copper }} />
                  </span>
                  <span className="text-[9.5px]" style={{ color: C.ivory }}>
                    {load}%
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Activité en temps réel — même panneau que App/Gaming/Robo. */}
        <div
          className="flex h-[268px] w-[clamp(226px,18vw,276px)] shrink-0 flex-col rounded-xl border px-3 py-[11px]"
          style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
        >
          <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
            <span className="text-[9.5px] tracking-[1.6px]" style={{ color: "#A7ADB5" }}>
              ACTIVITÉ EN TEMPS RÉEL
            </span>
            <Link href={ROUTES.activity} className="text-[9.5px]" style={{ color: C.copper }}>
              Tout voir
            </Link>
          </div>
          <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-[11px] overflow-y-auto py-2.5">
            {activityFeed.length === 0 ? (
              <p className="py-6 text-center text-[10px]" style={{ color: C.faint }}>
                Aucune activité récente.
              </p>
            ) : (
              activityFeed.slice(0, 12).map((ev) => (
                <div key={ev.id} className="flex items-start gap-2">
                  <span className="w-[29px] shrink-0 pt-[3px] text-[9.5px]" style={{ color: C.faint }}>
                    {ev.time}
                  </span>
                  <AgentAvatar agentId={ev.agent} name={ev.agent} size={24} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[11px] font-semibold" style={{ color: "#E8DFD4" }}>
                      {ev.agent}
                    </span>
                    <span className="block text-[10px] leading-[1.35]" style={{ color: C.muted }}>
                      {ev.action}
                    </span>
                    <span className="mt-px block text-[9px]" style={{ color: C.faint }}>
                      {ev.dept}
                    </span>
                  </span>
                  <span className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: (KIND_META[ev.kind] ?? KIND_META.create).color }} />
                </div>
              ))
            )}
          </div>
          <Link href={ROUTES.activity} className="rounded-lg border py-[7px] text-center text-[10.5px]" style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}>
            Voir toute l&apos;activité
          </Link>
        </div>
      </div>

      <div className="flex min-h-[clamp(340px,44vh,420px)] flex-1 gap-3">
        <div
          className="flex w-[clamp(176px,13.4vw,206px)] shrink-0 flex-col self-start rounded-xl border px-2.5 py-[11px]"
          style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
        >
          <div className="flex items-center justify-between border-b pb-[9px]" style={{ borderColor: C.lineSoft }}>
            <span className="text-[9.5px] tracking-[1.5px]" style={{ color: "#A7ADB5" }}>
              ÉQUIPE MARKETING
            </span>
            <span className="flex items-center gap-1 rounded-[10px] border px-[6px] py-px text-[9px]" style={{ borderColor: "rgba(140,200,150,.3)", color: C.onlineSoft }}>
              <span className="h-[5px] w-[5px] rounded-full" style={{ background: C.online }} />
              {activeCount > 0 ? "En ligne" : "En veille"} ▾
            </span>
          </div>
          <div className="alnua-scroll max-h-[240px] space-y-1 overflow-y-auto py-2">
            {agents.map((agent) => {
              const s = statuses[agent.id]?.status ?? "idle";
              const active = agent.id === selectedId;
              return (
                <button
                  key={agent.id}
                  type="button"
                  onClick={() => setSelectedId(agent.id)}
                  className="flex w-full items-center gap-2 rounded-lg px-1.5 py-1.5 text-left transition-colors"
                  style={active ? { background: "rgba(192,138,114,.12)" } : undefined}
                >
                  <AgentAvatar agentId={agent.id} name={agent.name} size={32} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[11px] font-medium" style={{ color: active ? C.copperLight : C.ivory }}>
                      {agent.name}
                    </span>
                    <span className="block truncate text-[9px]" style={{ color: C.faint }}>
                      {agent.role}
                    </span>
                  </span>
                  <span className="flex shrink-0 flex-col items-end gap-[3px]">
                    <span className="text-[9.5px]" style={{ color: C.dim }}>
                      {STATUS_LOAD[s]}%
                    </span>
                    <span className="h-[5px] w-[5px] rounded-full" style={{ background: STATUS_COLOR[s] }} />
                  </span>
                </button>
              );
            })}
          </div>
          <Link href={ROUTES.agents} className="rounded-lg border py-[6px] text-center text-[10px]" style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}>
            Voir toute l&apos;équipe
          </Link>
        </div>

        <div
          className="flex min-w-0 flex-1 flex-col gap-[11px] rounded-xl border px-[13px] py-3"
          style={{
            borderColor: C.lineStrong,
            background: "radial-gradient(120% 120% at 0% 0%, rgba(192,138,114,.08), rgba(19,22,27,.6) 55%)",
            boxShadow: "0 0 24px rgba(192,138,114,.07)",
          }}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <AgentAvatar agentId={selected.id} name={selected.name} size={56} ring />
              <div className="min-w-0">
                <div className="flex items-center gap-[7px]">
                  <span className="truncate text-[19px] font-semibold">{selected.name}</span>
                  <span className="text-[13px]" style={{ color: C.copperLight }}>
                    ✔
                  </span>
                </div>
                <p className="truncate text-[12px]" style={{ color: C.muted }}>
                  {selected.role}
                </p>
                <p className="mt-1 truncate text-[9.5px]" style={{ color: C.faint }}>
                  Spécialités : {selected.skills.join(" · ")}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1.5">
              <div className="flex items-center gap-3.5 text-[10px]">
                <span className="flex items-center gap-1.5" style={{ color: STATUS_COLOR[selStatus] }}>
                  <span className="h-[5px] w-[5px] rounded-full" style={{ background: STATUS_COLOR[selStatus] }} />
                  {STATUS_TEXT[selStatus]}
                </span>
                <Link
                  href={`${ROUTES.openroom}?agent=${encodeURIComponent(selected.id)}`}
                  className="rounded-[16px] border px-3 py-[5px] text-[10.5px]"
                  style={{ borderColor: C.lineStrong, color: "#E8DFD4" }}
                >
                  Ouvrir le profil complet ↗
                </Link>
              </div>
              <div className="flex gap-3.5 text-[10px]" style={{ color: C.dim }}>
                <span>⊕ Marketing</span>
                <span>⏱ {selected.skills.length} compétences</span>
              </div>
            </div>
          </div>

          <div className="flex min-h-0 flex-1 flex-col gap-[11px] min-[1240px]:flex-row">
            <MissionBox agent={selected} status={statuses[selected.id]} tickets={tickets} />
            <ChatPanel agent={selected} />
            <RecentTasksPanel tasks={agentTasks} />
          </div>
        </div>

        <ApercuPanel agent={selected} selLoad={selLoad} selStatus={selStatus} projects={projects} tickets={tickets} bureau="marketing" />
      </div>
    </div>
  );
}

export default function MarketingDepartmentV2Page() {
  return (
    <ConsoleProvider>
      <MarketingDepartmentView />
      <CooDrawer />
    </ConsoleProvider>
  );
}

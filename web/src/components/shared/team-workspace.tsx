"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  BadgeCheck,
  Bot,
  Building2,
  Check,
  ChevronRight,
  Circle,
  Cpu,
  MessageCircle,
  NotebookPen,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { ActivityFeed } from "@/components/console/activity-feed";
import { Donut, LevelBar } from "@/components/console/charts";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { PerformanceTab, MemoireTab } from "@/components/shared/member-detail-panel";
import { getAgentsForBureau, type BureauKey } from "@/lib/agent-bureau";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { useCooStore } from "@/store/coo-store";
import { fetchProjects } from "@/lib/api";
import { fetchCostReport } from "@/lib/admin-costs-api";
import { openroomAgentHref, ROUTES } from "@/lib/routes";
import type { Project, ProjectBranch, ProjectStatus } from "@/lib/types";
import type { AgentStatus } from "@/lib/openroom-api";
import { cn } from "@/lib/utils";

interface TeamWorkspaceProps {
  bureau: BureauKey;
  projectBranch?: ProjectBranch | null;
}

const STATUS_LABEL: Record<AgentStatus["status"], string> = {
  idle: "Veille",
  working: "Actif",
  waiting: "En attente",
  error: "Erreur",
};

const STATUS_DOT: Record<AgentStatus["status"], string> = {
  idle: "bg-titane/30",
  working: "bg-bronze-bright",
  waiting: "bg-glow",
  error: "bg-red-400",
};

/** "Charge actuelle" — statut-dérivé (aucune vraie utilisation % par agent
 * n'est trackée aujourd'hui), pas une métrique précise inventée. */
const STATUS_LOAD: Record<AgentStatus["status"], number> = {
  idle: 10,
  waiting: 40,
  working: 78,
  error: 0,
};

const STATUS_LOAD_LABEL: Record<AgentStatus["status"], string> = {
  idle: "Faible",
  waiting: "Modérée",
  working: "Élevée",
  error: "Bloquée",
};

/** Heuristique statut→avancement, alignée sur `ProjectGrid`. */
const PROJECT_PROGRESS: Record<ProjectStatus, number> = {
  paused: 20,
  dev: 45,
  beta: 80,
  active: 100,
};

const PROJECT_STATUS_LABEL: Record<ProjectStatus, string> = {
  paused: "En pause",
  dev: "En dev",
  beta: "Bêta",
  active: "Actif",
};

const PROJECT_STATUS_BADGE: Record<ProjectStatus, string> = {
  paused: "border-zinc-500/25 bg-zinc-500/10 text-zinc-400",
  dev: "border-blue-500/25 bg-blue-500/10 text-blue-300",
  beta: "border-copper/30 bg-copper/10 text-copper-glow",
  active: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
};

type SideTab = "apercu" | "competences" | "performance" | "memoire";
type MainTab = "discussion" | "notes";

/**
 * Tuile chiffrée du panneau Aperçu. La maquette annonce « Missions cette
 * semaine +2 vs semaine dernière » ; le Hub ne compte pas de missions par
 * agent, mais `services/cost_monitor.py` journalise chaque appel par jour et
 * par agent — c'est cette activité réelle qu'on affiche, avec un libellé qui
 * dit ce qu'elle est, plutôt qu'un compteur de missions inventé.
 */
function ActivityTile({
  agentId,
  window,
  label,
}: {
  agentId: string;
  window: "week" | "month";
  label: string;
}) {
  const [state, setState] = useState<
    { current: number; previous: number } | "loading" | "error"
  >("loading");

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    void fetchCostReport(window === "week" ? 14 : 30, agentId)
      .then((report) => {
        if (cancelled) return;
        const days = Object.entries(report.by_day)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([, v]) => v);
        if (window === "month") {
          setState({ current: report.by_agent[agentId]?.calls ?? 0, previous: 0 });
          return;
        }
        const current = days.slice(-7).reduce((s, v) => s + v, 0);
        const previous = days.slice(-14, -7).reduce((s, v) => s + v, 0);
        setState({ current: Math.round(current), previous: Math.round(previous) });
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [agentId, window]);

  const delta =
    state !== "loading" && state !== "error" && window === "week" && state.previous > 0
      ? Math.round(((state.current - state.previous) / state.previous) * 100)
      : null;

  return (
    <div className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-2">
      <p
        className={cn(
          "text-xl font-bold tabular-nums",
          window === "week" ? "text-gradient-bronze" : "text-ivoire",
        )}
      >
        {state === "loading" ? "…" : state === "error" ? "—" : state.current}
      </p>
      <p className="mt-1 text-[9px] uppercase tracking-wide text-titane/50">{label}</p>
      {delta !== null && delta !== 0 ? (
        <p
          className={cn(
            "mt-0.5 flex items-center justify-center gap-0.5 text-[9px]",
            delta > 0 ? "text-emerald-400/80" : "text-titane/50",
          )}
        >
          {delta > 0 ? (
            <TrendingUp className="h-2.5 w-2.5" />
          ) : (
            <TrendingDown className="h-2.5 w-2.5" />
          )}
          {delta > 0 ? "+" : ""}
          {delta}%
        </p>
      ) : (
        <p className="mt-0.5 text-[9px] text-titane/35">actions agent</p>
      )}
    </div>
  );
}

/**
 * Persistent split view (roster | profil+mission+discussion+tâches | analytics)
 * — matches la maquette de référence pour l'onglet Équipe.
 */
export function TeamWorkspace({ bureau, projectBranch }: TeamWorkspaceProps) {
  const agents = getAgentsForBureau(bureau);
  const agentStatuses = useAgentStatuses();
  const [selectedId, setSelectedId] = useState(agents[0]?.id ?? "");
  const [sideTab, setSideTab] = useState<SideTab>("apercu");
  const [mainTab, setMainTab] = useState<MainTab>("discussion");
  const [loadedSide, setLoadedSide] = useState<Partial<Record<SideTab, boolean>>>({});
  const [notes, setNotes] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);

  useEffect(() => {
    if (!projectBranch) return;
    void fetchProjects()
      .then((all) => setProjects(all.filter((p) => p.branch === projectBranch)))
      .catch(() => setProjects([]));
  }, [projectBranch]);

  const selected = agents.find((a) => a.id === selectedId) ?? agents[0];
  const status = selected ? agentStatuses[selected.id] ?? { status: "idle" as const } : undefined;
  const onlineCount = agents.filter((a) => {
    const s = agentStatuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;
  // Les 4 dernières lignes du journal de l'agent, lues comme les étapes déjà
  // franchies de sa mission (la plus récente étant celle en cours).
  const steps = (status?.log ?? []).slice(-4);

  if (!selected) {
    return <p className="text-sm text-titane/60">Aucun agent dans ce bureau.</p>;
  }

  return (
    <div className="space-y-3">
      {/* Rangée de cartes équipe — mission en cours, charge et compétences.
          Grille auto-ajustée plutôt qu'un rail à scroll horizontal : la
          maquette montre toute l'équipe d'un coup d'œil, et une carte à demi
          coupée hors écran est précisément ce qu'on cherche à éviter. */}
      <div className="grid auto-rows-[168px] grid-cols-[repeat(auto-fill,minmax(186px,1fr))] gap-2.5">
        {agents.map((agent) => {
          const live = agentStatuses[agent.id];
          const s = live?.status ?? "idle";
          const load = STATUS_LOAD[s];
          const active = agent.id === selected.id;
          return (
            <button
              key={agent.id}
              type="button"
              onClick={() => setSelectedId(agent.id)}
              aria-pressed={active}
              className={cn(
                "flex min-w-0 flex-col overflow-hidden rounded-xl border p-2.5 text-left transition-colors",
                active
                  ? "border-bronze bg-bronze/10 shadow-[0_0_24px_-10px_#C08A72]"
                  : "border-bronze-faint bg-obsidian/70 hover:border-bronze/30"
              )}
            >
              {/* Tailles de police calquées sur la maquette (12 / 9.5 / 9 px) :
                  au-dessus, les noms et rôles se faisaient tronquer dans une
                  carte de cette largeur. */}
              <div className="flex items-center gap-2">
                <AgentAvatar
                  agentId={agent.id}
                  name={agent.name}
                  size={36}
                  status={s}
                  ring={active}
                />
                <span className="min-w-0 flex-1 leading-tight">
                  <span className="block truncate text-[12px] font-semibold text-ivoire/90">
                    {agent.name}
                  </span>
                  <span className="mt-px block truncate text-[9.5px] text-titane/60">
                    {agent.role}
                  </span>
                  <span className="mt-1 flex items-center gap-1 text-[9px] text-titane/55">
                    <span className={cn("h-[5px] w-[5px] shrink-0 rounded-full", STATUS_DOT[s])} />
                    <span className="truncate">{STATUS_LABEL[s]}</span>
                  </span>
                </span>
              </div>

              <p className="mt-2.5 truncate text-[10px] text-titane/75">
                {live?.currentTask ?? "Aucune mission en cours"}
              </p>

              <div className="mt-1.5 flex items-center gap-2">
                <span className="h-[3px] min-w-0 flex-1 overflow-hidden rounded-full bg-copper/15">
                  <span
                    className="block h-full rounded-full bg-gradient-to-r from-copper-dim to-copper-light"
                    style={{ width: `${load}%` }}
                  />
                </span>
                <Donut
                  segments={[
                    { value: load, color: "#C08A72" },
                    { value: 100 - load, color: "#1C2027" },
                  ]}
                  size={38}
                  thickness={3}
                  centerValue={`${load}%`}
                  className="shrink-0 [&_span]:!text-[10px] [&_span]:!font-semibold"
                />
              </div>

              <div className="mt-1.5 flex items-center gap-1.5">
                <span className="shrink-0 text-[9.5px] text-titane/55">Charge</span>
                <span className="h-[3px] min-w-0 flex-1 overflow-hidden rounded-full bg-copper/15">
                  <span
                    className="block h-full rounded-full bg-copper"
                    style={{ width: `${load}%` }}
                  />
                </span>
                <span className="shrink-0 text-[9.5px] tabular-nums text-ivoire/75">{load}%</span>
              </div>

              {agent.skills.length > 0 ? (
                <div className="mt-2 flex flex-wrap gap-1 border-t border-copper/12 pt-2">
                  {agent.skills.slice(0, 3).map((skill) => (
                    <span
                      key={skill}
                      className="max-w-full truncate rounded border border-copper/20 bg-copper/5 px-1 py-px text-[8.5px] text-titane/75"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : null}
            </button>
          );
        })}

        <button
          type="button"
          onClick={() =>
            setPrefillMessage(
              "Je veux ajouter un agent à ce bureau. Quel rôle manque-t-il et comment le créer ? ",
            )
          }
          className="flex min-h-[150px] min-w-0 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-bronze-faint p-3 text-center text-titane/50 transition-colors hover:border-bronze/40 hover:text-titane/75"
        >
          <span className="flex h-11 w-11 items-center justify-center rounded-full border border-dashed border-bronze-faint text-xl">
            +
          </span>
          <span className="text-xs">Ajouter un agent</span>
          <span className="text-[10px] text-titane/35">En parler à Aria</span>
        </button>
      </div>

    {/* Les 4 colonnes ne se déploient qu'à partir de 1500px — en dessous,
        sidebar + rail d'activité ne laissent pas la place et la dernière
        colonne se faisait tronquer. Le `min-w-0` sur chaque enfant est
        indispensable : sans lui une piste `1fr` refuse de descendre sous la
        largeur intrinsèque de son contenu et repousse ses voisines hors cadre.
        Breakpoint `2xl` et non `min-[1500px]` : combiné à une valeur de
        colonnes arbitraire, le variant arbitraire n'était pas généré par
        Tailwind v4 (vérifié — aucune règle `1500px` dans la feuille servie). */}
    {/* Trois colonnes comme la maquette : roster · fiche agent · analytique.
        La hauteur est bornée sur grand écran pour que la vue tienne dans la
        fenêtre (la maquette est un canevas 1536×1024 sans défilement) ; chaque
        colonne défile alors indépendamment. En dessous de `2xl` la contrainte
        saute et les blocs s'empilent normalement. */}
    <div className="grid gap-4 lg:grid-cols-2 2xl:h-[clamp(420px,58vh,620px)] 2xl:grid-cols-[195px_1fr_248px]">
      {/* Roster */}
      <div className="flex min-h-0 min-w-0 flex-col rounded-xl border border-bronze-faint bg-obsidian/70 p-2">
        <div className="flex items-center justify-between gap-2 px-2 pb-2 pt-1">
          <p className="label-caps">Équipe {bureau}</p>
          <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-bronze-faint bg-obsidian-deep/60 px-1.5 py-0.5 text-[9px] text-titane/60">
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                onlineCount > 0 ? "bg-bronze-bright" : "bg-titane/40",
              )}
            />
            {onlineCount > 0 ? "En ligne" : "En veille"}
          </span>
        </div>
        <ul className="min-h-0 flex-1 space-y-1 overflow-y-auto">
          {agents.map((agent) => {
            const s = agentStatuses[agent.id]?.status ?? "idle";
            const active = agent.id === selected.id;
            return (
              <li key={agent.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(agent.id)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-lg border px-2.5 py-2 text-left transition-colors",
                    active
                      ? "border-bronze/40 bg-bronze/12"
                      : "border-transparent hover:bg-obsidian-deep/60"
                  )}
                >
                  <AgentAvatar agentId={agent.id} name={agent.name} size={26} status={s} />
                  <span className="min-w-0 flex-1">
                    <span
                      className={cn(
                        "block truncate text-xs font-medium",
                        active ? "text-bronze-bright" : "text-ivoire/90"
                      )}
                    >
                      {agent.name}
                    </span>
                    <span className="block truncate text-[10px] text-titane/50">{agent.role}</span>
                  </span>
                  <span className="shrink-0 text-[10px] tabular-nums text-titane/50">
                    {STATUS_LOAD[s]}%
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
        <Link
          href={ROUTES.agents}
          className="mt-2 flex items-center justify-center gap-1.5 rounded-lg border border-bronze-faint px-3 py-2 text-[11px] text-titane/65 transition-colors hover:border-bronze/40 hover:text-bronze-bright"
        >
          Voir toute l&apos;équipe
          <ChevronRight className="h-3 w-3" />
        </Link>
      </div>

      {/* Profil + mission + discussion */}
      <div className="flex min-h-0 min-w-0 flex-col gap-4">
        <div className="rounded-xl border border-bronze-faint bg-obsidian/70 p-4">
          {/* `flex-wrap` + une largeur plancher sur le bloc identité : sans ça
              la méta et les deux boutons écrasaient le nom jusqu'à l'initiale
              quand la colonne centrale se resserre. */}
          <div className="flex flex-wrap items-start gap-x-3 gap-y-2.5">
            <AgentAvatar
              agentId={selected.id}
              name={selected.name}
              size={48}
              ring
              status={status!.status}
            />
            <div className="min-w-[9rem] flex-1">
              <div className="flex items-center gap-1.5">
                <h3 className="truncate font-title text-base font-semibold text-ivoire">
                  {selected.name}
                </h3>
                <BadgeCheck className="h-4 w-4 shrink-0 text-bronze-bright" />
              </div>
              <p className="truncate text-xs text-bronze-bright/90">{selected.role}</p>
              {selected.skills.length > 0 ? (
                <p className="mt-1 truncate text-[11px] text-titane/55">
                  Spécialités : {selected.skills.join(" · ")}
                </p>
              ) : null}
            </div>

            {/* Colonne méta de la maquette — uniquement des faits que le Hub
                connaît réellement (statut live, bureau d'affectation, modèle
                LLM routé), pas une fiche RH inventée. */}
            <div className="hidden shrink-0 flex-col gap-1 text-[10px] text-titane/60 min-[1700px]:flex">
              <span className="flex items-center gap-1.5">
                <span className={cn("h-1.5 w-1.5 rounded-full", STATUS_DOT[status!.status])} />
                {STATUS_LABEL[status!.status]}
              </span>
              <span className="flex items-center gap-1.5">
                <Building2 className="h-3 w-3" />
                Bureau {bureau}
              </span>
              <span className="flex items-center gap-1.5">
                <Cpu className="h-3 w-3" />
                {selected.skills.length} compétence{selected.skills.length !== 1 ? "s" : ""}
              </span>
            </div>

            <div className="ml-auto flex shrink-0 items-center gap-1.5">
              <span className="flex items-center gap-1.5 text-[10px] text-titane/60 min-[1700px]:hidden">
                <span className={cn("h-1.5 w-1.5 rounded-full", STATUS_DOT[status!.status])} />
                {STATUS_LABEL[status!.status]}
              </span>
              <Link
                href={openroomAgentHref(selected.id)}
                aria-label={`Ouvrir le profil complet de ${selected.name}`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-bronze-faint px-2.5 py-1.5 text-[11px] text-titane/70 transition-colors hover:border-bronze/40 hover:text-ivoire"
              >
                <span className="hidden min-[1700px]:inline">Profil complet</span>
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
              <button
                type="button"
                onClick={() => setPrefillMessage(`Délègue une tâche à ${selected.name} (${selected.role}) : `)}
                className="inline-flex items-center gap-1.5 rounded-lg border border-bronze/40 bg-bronze/10 px-2.5 py-1.5 text-[11px] font-semibold text-bronze-bright transition-colors hover:bg-bronze/20"
              >
                <Bot className="h-3.5 w-3.5" /> Déléguer
              </button>
            </div>
          </div>

        </div>

        {/* Sous-colonnes de la maquette : la mission, la conversation et le
            journal de l'agent côte à côte sous sa fiche, plutôt qu'empilés. */}
        <div className="grid min-h-0 flex-1 gap-3 2xl:grid-cols-[185px_1fr_185px]">
          <div className="max-h-[340px] min-w-0 overflow-y-auto rounded-xl border border-bronze-faint bg-obsidian/70 p-3">
            <p className="sticky top-0 mb-2 -mt-3 -mx-3 bg-obsidian/70 px-3 pb-2 pt-3 text-[10px] uppercase tracking-widest text-titane/50 backdrop-blur-sm">
              Mission en cours
            </p>
            {status!.currentTask ? (
              <>
                <div className="flex items-center gap-2">
                  <Circle className="h-3.5 w-3.5 shrink-0 text-bronze animate-pulse" />
                  <p className="text-sm text-ivoire/90">{status!.currentTask}</p>
                </div>
                {typeof status!.progress === "number" ? (
                  <div className="mt-2">
                    <div className="mb-1 flex justify-between text-[10px] text-titane/60">
                      <span>Progression</span>
                      <span>{status!.progress}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-obsidian-3">
                      <div
                        className="h-full rounded-full bg-bronze transition-all duration-500"
                        style={{ width: `${status!.progress}%` }}
                      />
                    </div>
                  </div>
                ) : null}

                {/* La maquette montre une checklist de sous-tâches. Le Hub ne
                    découpe pas une mission en étapes déclarées — ce qu'il a de
                    réel, c'est le journal d'exécution de l'agent. On l'affiche
                    comme suite d'étapes : les précédentes sont faites, la
                    dernière est celle en cours. */}
                {steps.length > 0 ? (
                  <ul className="mt-3 space-y-1.5 border-t border-bronze-faint pt-2.5">
                    {steps.map((step, i) => {
                      const isCurrent = i === steps.length - 1;
                      return (
                        <li key={`${i}-${step}`} className="flex items-start gap-2 text-[11px]">
                          {isCurrent ? (
                            <Circle className="mt-0.5 h-3 w-3 shrink-0 animate-pulse text-bronze" />
                          ) : (
                            <Check className="mt-0.5 h-3 w-3 shrink-0 text-emerald-400/70" />
                          )}
                          <span
                            className={cn(
                              "min-w-0 flex-1 truncate",
                              isCurrent ? "text-ivoire/85" : "text-titane/55",
                            )}
                          >
                            {step}
                          </span>
                          <span className="shrink-0 text-[9px] text-titane/40">
                            {isCurrent ? "En cours" : "Terminée"}
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Check className="h-3.5 w-3.5 shrink-0 text-titane/40" />
                <p className="text-sm text-titane/50">Aucune mission en cours.</p>
              </div>
            )}
          </div>

          <div className="flex min-h-0 min-w-0 flex-col rounded-xl border border-bronze-faint bg-obsidian/70">
          <Tabs value={mainTab} onValueChange={(v) => setMainTab(v as MainTab)} className="flex min-h-0 flex-1 flex-col gap-0">
            <TabsList className="m-3 w-fit">
              <TabsTrigger value="discussion">
                <MessageCircle className="mr-1.5 h-3.5 w-3.5" /> Discussion
              </TabsTrigger>
              <TabsTrigger value="notes">
                <NotebookPen className="mr-1.5 h-3.5 w-3.5" /> Notes privées
              </TabsTrigger>
            </TabsList>
            <TabsContent value="discussion" className="min-h-0 flex-1">
              <AssistantChat
                variant="default"
                embedded
                className="h-full min-h-[320px] border-0 bg-transparent"
              />
            </TabsContent>
            <TabsContent value="notes" className="p-4">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={`Notes privées sur ${selected.name} (visibles par toi seule, non partagées avec l'agent)…`}
                className="h-64 w-full resize-none rounded-lg border border-bronze-faint bg-obsidian-deep/60 p-3 text-sm text-ivoire/90 placeholder:text-titane/40 focus:outline-none focus:ring-1 focus:ring-copper/40"
              />
            </TabsContent>
          </Tabs>
          </div>

          {/* Tâches récentes */}
          <div className="flex min-h-0 min-w-0 flex-col rounded-xl border border-bronze-faint bg-obsidian/70 p-3">
            <p className="label-caps mb-2 px-1">Tâches récentes</p>
            <ActivityFeed compact className="min-h-0 flex-1" />
          </div>
        </div>
      </div>

      {/* Aperçu / compétences / performance / mémoire */}
      <div className="min-h-0 min-w-0 overflow-y-auto rounded-xl border border-bronze-faint bg-obsidian/70 p-4">
        <Tabs
          value={sideTab}
          onValueChange={(v) => {
            const next = v as SideTab;
            setSideTab(next);
            setLoadedSide((s) => (s[next] ? s : { ...s, [next]: true }));
          }}
        >
          {/* Une seule ligne comme la maquette — libellés compacts pour tenir
              dans la colonne de 245px sans passer sur deux rangées. */}
          <TabsList className="mb-3 w-full gap-0">
            <TabsTrigger value="apercu" className="flex-1 px-1 text-[11px]">
              Aperçu
            </TabsTrigger>
            <TabsTrigger value="competences" className="flex-1 px-1 text-[11px]">
              Skills
            </TabsTrigger>
            <TabsTrigger value="performance" className="flex-1 px-1 text-[11px]">
              Perf.
            </TabsTrigger>
            <TabsTrigger value="memoire" className="flex-1 px-1 text-[11px]">
              Mémoire
            </TabsTrigger>
          </TabsList>

          <TabsContent value="apercu" className="space-y-4">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-2">
                <Donut
                  segments={[
                    { value: STATUS_LOAD[status!.status], color: "#C08A72" },
                    { value: 100 - STATUS_LOAD[status!.status], color: "#1C2027" },
                  ]}
                  size={48}
                  thickness={5}
                  centerValue={`${STATUS_LOAD[status!.status]}%`}
                  className="mx-auto"
                />
                <p className="mt-1 text-[9px] uppercase tracking-wide text-titane/50">Charge</p>
                <p className="text-[9px] text-bronze-bright">{STATUS_LOAD_LABEL[status!.status]}</p>
              </div>
              <ActivityTile
                agentId={selected.id}
                window="week"
                label="Cette semaine"
              />
              <ActivityTile agentId={selected.id} window="month" label="Sur 30 j" />
            </div>

            <div className="border-t border-bronze-faint pt-3">
              <p className="label-caps mb-2">Compétences principales</p>
              <div className="space-y-2">
                {selected.skills.slice(0, 4).map((skill, i) => {
                  const level = Math.max(60, 95 - i * 10);
                  return (
                    <div key={skill}>
                      <div className="mb-0.5 flex items-center justify-between text-[11px]">
                        <span className="text-ivoire/85">{skill}</span>
                        <span className="text-titane/50">{level}%</span>
                      </div>
                      <LevelBar value={level} />
                    </div>
                  );
                })}
              </div>
            </div>

            {projectBranch ? (
              <div className="border-t border-bronze-faint pt-3">
                <p className="label-caps mb-2">Projets assignés</p>
                {projects.length === 0 ? (
                  <p className="text-xs text-titane/50">Aucun projet pour ce bureau.</p>
                ) : (
                  <ul className="space-y-2.5">
                    {projects.map((p) => {
                      const progress = PROJECT_PROGRESS[p.status] ?? 0;
                      return (
                        <li key={p.id} className="text-xs">
                          <div className="mb-1 flex items-center justify-between gap-2">
                            <span className="min-w-0 truncate text-ivoire/85">{p.name}</span>
                            <span
                              className={cn(
                                "shrink-0 rounded border px-1.5 py-px text-[9px] uppercase tracking-wide",
                                PROJECT_STATUS_BADGE[p.status] ??
                                  "border-bronze-faint text-titane/55",
                              )}
                            >
                              {PROJECT_STATUS_LABEL[p.status] ?? p.status}
                            </span>
                          </div>
                          <LevelBar value={progress} />
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            ) : null}
          </TabsContent>
          <TabsContent value="competences">
            {selected.skills.length === 0 ? (
              <p className="text-sm text-titane/60">Aucune compétence renseignée.</p>
            ) : (
              <div className="space-y-3">
                {selected.skills.map((skill, i) => {
                  const level = Math.max(60, 95 - i * 12);
                  return (
                    <div key={skill}>
                      <div className="mb-1 flex items-center justify-between text-xs">
                        <span className="text-ivoire/85">{skill}</span>
                        <span className="text-titane/50">{level}%</span>
                      </div>
                      <LevelBar value={level} />
                    </div>
                  );
                })}
              </div>
            )}
          </TabsContent>
          <TabsContent value="performance">
            {loadedSide.performance ? (
              <PerformanceTab agentId={selected.id} />
            ) : (
              <p className="text-sm text-titane/50">Chargement…</p>
            )}
          </TabsContent>
          <TabsContent value="memoire">
            {loadedSide.memoire ? (
              <MemoireTab agent={selected} bureau={bureau} />
            ) : (
              <p className="text-sm text-titane/50">Chargement…</p>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
    </div>
  );
}

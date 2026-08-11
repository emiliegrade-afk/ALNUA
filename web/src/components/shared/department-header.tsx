"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  AppWindow,
  Bot,
  Calculator,
  Compass,
  Crown,
  FlaskConical,
  Gamepad2,
  MoreVertical,
  Megaphone,
  Network,
  Palette,
  Scale,
  Ticket,
  UserRound,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useHubNavigate } from "@/components/layout/hub-navigation";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauKey } from "@/lib/agent-bureau";
import { useCooStore } from "@/store/coo-store";
import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

const DEPT_ICONS: Record<string, LucideIcon> = {
  hub: Compass,
  secretary: UserRound,
  legal: Scale,
  ceo: Crown,
  rd: FlaskConical,
  app: AppWindow,
  gaming: Gamepad2,
  robo: Network,
  marketing: Megaphone,
  finances: Calculator,
  analytics: Compass,
  brand: Palette,
  academy: Users,
};

interface DepartmentHeaderProps {
  dept: DeptKey;
  title: string;
  subtitle?: string;
  breadcrumb?: string;
  /** Renseigné → pastille « N agents actifs » et délégation contextualisée. */
  bureau?: BureauKey;
  className?: string;
}

/** Titre bicolore de la maquette : le mot distinctif passe en cuivre, le
 * qualificatif reste en titane. « Pôle App » → PÔLE **APP**. */
function splitTitle(title: string): [string, string] {
  const parts = title.trim().split(/\s+/);
  if (parts.length < 2) return ["", title];
  return [parts.slice(0, -1).join(" "), parts[parts.length - 1]];
}

export function DepartmentHeader({
  dept,
  title,
  subtitle,
  breadcrumb,
  bureau,
  className,
}: DepartmentHeaderProps) {
  const { navigate } = useHubNavigate();
  const colors = DEPT_COLORS[dept];
  const crumb = breadcrumb ?? title;
  const Icon = DEPT_ICONS[dept] ?? Compass;
  const [lead, accent] = splitTitle(title);

  const agentStatuses = useAgentStatuses();
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const agents = bureau ? getAgentsForBureau(bureau) : [];
  const activeCount = agents.filter((a) => {
    const s = agentStatuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;

  useEffect(() => {
    if (!menuOpen) return;
    function onDown(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  return (
    <header className={cn("bureau-header", className)}>
      <nav className="mb-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-bronze-faint bg-obsidian/70 px-2.5 py-1.5 text-[11px] font-medium uppercase tracking-[0.12em] text-titane/70 transition hover:border-bronze/40 hover:text-ivoire"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Lobby
        </button>
        <span className="text-titane/35">/</span>
        <span
          className="text-[11px] font-medium uppercase tracking-[0.14em]"
          style={{ color: colors.main }}
        >
          {crumb}
        </span>
      </nav>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-4">
          <span
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border bg-obsidian-deep/80"
            style={{ borderColor: colors.border, boxShadow: `inset 0 0 24px -8px ${colors.main}` }}
          >
            <Icon className="h-6 w-6" style={{ color: colors.main }} />
          </span>
          <div className="min-w-0">
            <h1 className="font-title text-2xl font-semibold uppercase tracking-[0.14em] sm:text-3xl">
              {lead ? <span className="text-titane/70">{lead} </span> : null}
              <span className="text-gradient-bronze">{accent}</span>
            </h1>
            {subtitle ? (
              <p className="mt-1.5 font-body text-sm text-titane/70">{subtitle}</p>
            ) : null}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {bureau ? (
            <span className="inline-flex items-center gap-2 rounded-full border border-bronze-faint bg-obsidian/70 px-3 py-1.5 text-xs text-titane/75">
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  activeCount > 0 ? "animate-alnua-pulse bg-bronze-bright" : "bg-titane/40",
                )}
              />
              {activeCount} agent{activeCount !== 1 ? "s" : ""} actif
              {activeCount !== 1 ? "s" : ""}
              <span className="text-titane/35">/ {agents.length}</span>
            </span>
          ) : null}

          {bureau ? (
            <button
              type="button"
              onClick={() =>
                setPrefillMessage(
                  `Confie une mission à l'équipe ${title} (${agents.length} agents) : `,
                )
              }
              className="inline-flex items-center gap-1.5 rounded-lg border border-bronze/40 bg-bronze/10 px-3 py-1.5 text-xs font-semibold text-bronze-bright transition-colors hover:bg-bronze/20"
            >
              <Bot className="h-3.5 w-3.5" />
              Confier une mission
            </button>
          ) : null}

          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((v) => !v)}
              aria-expanded={menuOpen}
              aria-haspopup="menu"
              aria-label="Autres actions du département"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-bronze-faint bg-obsidian/70 text-titane/70 transition-colors hover:border-bronze/40 hover:text-ivoire"
            >
              <MoreVertical className="h-4 w-4" />
            </button>
            {menuOpen ? (
              <div
                role="menu"
                className="absolute right-0 top-[calc(100%+0.4rem)] z-20 w-56 overflow-hidden rounded-xl border border-bronze-faint bg-obsidian-deep/95 shadow-[0_16px_48px_rgba(0,0,0,0.6)] backdrop-blur-xl"
              >
                <Link
                  href={ROUTES.agents}
                  role="menuitem"
                  className="flex items-center gap-2.5 px-4 py-2.5 text-xs text-titane/75 transition-colors hover:bg-obsidian hover:text-ivoire"
                >
                  <Users className="h-3.5 w-3.5 shrink-0" />
                  Tout le roster d&apos;agents
                </Link>
                <Link
                  href={ROUTES.tickets}
                  role="menuitem"
                  className="flex items-center gap-2.5 px-4 py-2.5 text-xs text-titane/75 transition-colors hover:bg-obsidian hover:text-ivoire"
                >
                  <Ticket className="h-3.5 w-3.5 shrink-0" />
                  Tous les tickets
                </Link>
                <Link
                  href={ROUTES.settings}
                  role="menuitem"
                  className="flex items-center gap-2.5 border-t border-bronze-faint px-4 py-2.5 text-xs text-titane/75 transition-colors hover:bg-obsidian hover:text-ivoire"
                >
                  <Bot className="h-3.5 w-3.5 shrink-0" />
                  Configurer les agents
                </Link>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="mt-5 h-px w-full bg-gradient-to-r from-bronze/30 via-bronze/20 to-transparent" />
    </header>
  );
}

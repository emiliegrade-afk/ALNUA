"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  FileText,
  Scale,
  Target,
} from "lucide-react";
import {
  SiegeBadge,
  SiegePageHeader,
  SiegePanel,
  SiegeQuickLink,
  SiegeRingStat,
} from "@/components/siege/siege-ui";
import { SiegeLifeLinks } from "@/components/shared/siege-life-links";
import { fetchTodayBriefing, type DailyBriefing } from "@/lib/briefing-api";
import { ROUTES } from "@/lib/routes";

/** Bureau CEO — données live only (plus d’objectifs / réunions / % inventés). */
export function CeoCommandView() {
  const [briefing, setBriefing] = useState<DailyBriefing | null>(null);

  useEffect(() => {
    void fetchTodayBriefing({ ensure: false, timeoutMs: 8_000 })
      .then(setBriefing)
      .catch(() => setBriefing(null));
  }, []);

  const pending = briefing?.pending_count ?? 0;
  const urgent = briefing?.urgent_count ?? 0;
  const summaryLine = briefing?.summary?.trim();
  const ticketTitles =
    briefing?.raw_data?.tickets?.slice(0, 3).map((t) => t.title).filter(Boolean) ?? [];

  return (
    <div className="flex flex-col gap-4">
      <SiegePageHeader
        title="BUREAU DU CEO"
        accent="EMILIE"
        subtitle="Tableau de bord exécutif · décisions live · pas de métriques fictives"
        trailing={<SiegeLifeLinks />}
      />

      <div className="grid gap-4 lg:grid-cols-5">
        <SiegePanel title="Dashboard exécutif" className="lg:col-span-3">
          <div className="grid flex-1 grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
            <SiegeRingStat
              label="En attente"
              value={String(pending || "—")}
              hint={urgent ? `${urgent} critique(s)` : "brief du jour"}
            />
            <SiegeRingStat
              label="Critiques"
              value={String(urgent || "0")}
              hint="depuis briefing"
            />
            <SiegeRingStat label="Agents" value="53" hint="roster Hub" />
            <SiegeRingStat
              label="Brief"
              value={briefing ? "OK" : "—"}
              hint={briefing ? "chargé" : "indisponible"}
            />
          </div>
          {summaryLine ? (
            <p className="mt-4 border-t border-copper/10 pt-3 text-[12px] leading-relaxed text-titanium/80">
              {summaryLine}
            </p>
          ) : (
            <p className="mt-4 border-t border-copper/10 pt-3 text-[12px] text-titanium/50">
              Pas de résumé briefing — génère-en un depuis{" "}
              <Link href={ROUTES.briefing} className="text-copper hover:underline">
                /briefing
              </Link>
              .
            </p>
          )}
        </SiegePanel>

        <SiegePanel title="Priorités CEO" className="lg:col-span-2">
          <ul className="space-y-2.5 text-[12px] text-ivory/85">
            <li>
              <Link href={ROUTES.ceo} className="text-copper hover:underline">
                Valider dossiers R&D en file
              </Link>
            </li>
            <li>
              <Link href={ROUTES.rd} className="text-copper hover:underline">
                Ouvrir le lab R&D
              </Link>
            </li>
            <li>
              <Link href={ROUTES.trust} className="text-copper hover:underline">
                Trust & Review Board
              </Link>
            </li>
            <li>
              <Link href={ROUTES.finances} className="text-copper hover:underline">
                Coûts & finances
              </Link>
            </li>
          </ul>
          <p className="mt-3 text-[10px] text-titanium/45">
            Les barres d’objectifs % ont été retirées (données non branchées).
          </p>
        </SiegePanel>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <SiegePanel
          title="Alertes critiques"
          action={
            <Link href={ROUTES.activity} className="text-[10px] text-copper hover:underline">
              Activité →
            </Link>
          }
        >
          <ul className="space-y-2.5">
            {urgent > 0 ? (
              <li className="flex items-start gap-2 text-[12px] text-ivory/85">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-danger" />
                <span className="min-w-0 flex-1">
                  {urgent} alerte{urgent > 1 ? "s" : ""} urgente{urgent > 1 ? "s" : ""} dans le
                  brief
                </span>
                <SiegeBadge tone="danger">Critique</SiegeBadge>
              </li>
            ) : (
              <li className="flex items-start gap-2 text-[12px] text-ivory/85">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-copper/60" />
                <span className="min-w-0 flex-1">Aucune alerte urgente live</span>
                <SiegeBadge tone="ok">OK</SiegeBadge>
              </li>
            )}
          </ul>
        </SiegePanel>

        <SiegePanel
          title="Tickets / suivi brief"
          action={
            <Link href={ROUTES.briefing} className="text-[10px] text-copper hover:underline">
              Brief →
            </Link>
          }
        >
          {ticketTitles.length > 0 ? (
            <ul className="space-y-2.5">
              {ticketTitles.map((d, i) => (
                <li
                  key={`${d}-${i}`}
                  className="flex items-center justify-between gap-2 text-[12px] text-ivory/85"
                >
                  <span className="min-w-0 truncate">{d}</span>
                  <SiegeBadge tone="ok">Suivi</SiegeBadge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[12px] text-titanium/55">
              Aucun ticket dans le briefing actuel.
            </p>
          )}
        </SiegePanel>
      </div>

      <div className="flex flex-wrap gap-2">
        <SiegeQuickLink
          href={ROUTES.briefing}
          label="Brief du jour"
          icon={<Target className="h-3.5 w-3.5" />}
        />
        <SiegeQuickLink
          href={ROUTES.hub}
          label="Direction"
          icon={<CheckCircle2 className="h-3.5 w-3.5" />}
        />
        <SiegeQuickLink
          href={ROUTES.secretary}
          label="Secrétariat"
          icon={<FileText className="h-3.5 w-3.5" />}
        />
        <SiegeQuickLink
          href={ROUTES.legal}
          label="Juridique"
          icon={<Scale className="h-3.5 w-3.5" />}
        />
        <SiegeQuickLink
          href={ROUTES.finances}
          label="Finances"
          icon={<Calendar className="h-3.5 w-3.5" />}
        />
      </div>
    </div>
  );
}

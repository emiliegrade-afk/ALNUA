"use client";

import { formatDistanceToNow, isPast, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import { Badge } from "@/components/ui/badge";
import {
  avatarColor,
  initials,
  partnerStatusLabel,
  partnerTypeLabel,
  statusBadgeStyle,
  typeBadgeStyle,
} from "@/components/partnerships/partnerships.constants";
import type { Partner } from "@/lib/partnerships-api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface PartnerCardProps {
  partner: Partner;
  projects: Record<string, Project>;
  selected: boolean;
  onClick: () => void;
}

export function PartnerCard({
  partner,
  projects,
  selected,
  onClick,
}: PartnerCardProps) {
  const followupOverdue =
    partner.next_followup &&
    isPast(parseISO(partner.next_followup + "T23:59:59"));

  const lastContact = partner.last_contact_date
    ? formatDistanceToNow(parseISO(partner.last_contact_date), {
        addSuffix: true,
        locale: fr,
      })
    : null;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full rounded-xl border p-3 text-left transition",
        selected
          ? "border-copper/40 bg-copper/5"
          : "border-white/10 bg-surface/40 hover:border-white/20"
      )}
    >
      <div className="flex gap-3">
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white",
            avatarColor(partner.name)
          )}
        >
          {initials(partner.name)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="truncate font-medium text-ivory">{partner.name}</span>
            <Badge
              variant="outline"
              className={cn("text-[10px]", typeBadgeStyle(partner.type))}
            >
              {partnerTypeLabel(partner.type)}
            </Badge>
          </div>
          <div className="mt-1 flex flex-wrap gap-1">
            <Badge variant="outline" className="text-[10px] border-white/10">
              {partner.direction === "outbound" ? "→ Sortant" : "← Entrant"}
            </Badge>
            <Badge
              variant="outline"
              className={cn("text-[10px]", statusBadgeStyle(partner.status))}
            >
              {partnerStatusLabel(partner.status)}
            </Badge>
          </div>
          {partner.project_ids.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-1">
              {partner.project_ids.slice(0, 3).map((id) => (
                <span
                  key={id}
                  className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-titanium"
                >
                  {projects[id]?.name ?? "Projet"}
                </span>
              ))}
            </div>
          ) : null}
          {partner.audience_size ? (
            <p className="mt-1 text-[11px] text-titanium">
              ~{partner.audience_size.toLocaleString("fr-FR")} abonnés
            </p>
          ) : null}
          {partner.next_followup ? (
            <p
              className={cn(
                "mt-1 text-[11px]",
                followupOverdue ? "text-red-400" : "text-titanium"
              )}
            >
              Relance le {partner.next_followup}
            </p>
          ) : null}
          {lastContact ? (
            <p className="mt-0.5 text-[10px] text-titanium/70">
              Dernier contact {lastContact}
            </p>
          ) : null}
        </div>
      </div>
    </button>
  );
}

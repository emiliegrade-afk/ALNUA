"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Handshake, Loader2, Plus } from "lucide-react";
import { PartnerCard } from "@/components/partnerships/partner-card";
import { PartnerCreateModal } from "@/components/partnerships/partner-create-modal";
import { PartnerDetailPanel } from "@/components/partnerships/partner-detail-panel";
import {
  PARTNER_TYPES,
  partnerTypeLabel,
} from "@/components/partnerships/partnerships.constants";
import { RequestsTab } from "@/components/partnerships/requests-tab";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { fetchProjects } from "@/lib/api";
import {
  fetchPartners,
  fetchPartnershipStats,
  type Partner,
  type PartnershipStats,
} from "@/lib/partnerships-api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

type MainTab = "all" | "active" | "prospects" | "affiliates" | "requests";

export function PartnershipsView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [partners, setPartners] = useState<Partner[]>([]);
  const [stats, setStats] = useState<PartnershipStats | null>(null);
  const [loading, setLoading] = useState(true);

  const [mainTab, setMainTab] = useState<MainTab>("all");
  const [directionFilter, setDirectionFilter] = useState<string>("all");
  const [typeFilters, setTypeFilters] = useState<string[]>([]);
  const [projectFilter, setProjectFilter] = useState("all");

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  const projectMap = useMemo(
    () => Object.fromEntries(projects.map((p) => [p.id, p])),
    [projects]
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, s] = await Promise.all([
        fetchPartners({
          direction:
            directionFilter !== "all" ? directionFilter : undefined,
          project_id: projectFilter !== "all" ? projectFilter : undefined,
        }),
        fetchPartnershipStats(),
      ]);
      setPartners(p);
      setStats(s);
    } catch {
      setPartners([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [directionFilter, projectFilter]);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    if (mainTab !== "requests") load();
  }, [load, mainTab]);

  const filteredPartners = useMemo(() => {
    let list = partners;
    if (mainTab === "active") {
      list = list.filter((p) => p.status === "active");
    } else if (mainTab === "prospects") {
      list = list.filter((p) =>
        ["prospect", "contacted", "in_discussion"].includes(p.status)
      );
    } else if (mainTab === "affiliates") {
      list = list.filter((p) => p.type === "affiliate");
    }
    if (typeFilters.length) {
      list = list.filter((p) => typeFilters.includes(p.type));
    }
    return list;
  }, [partners, mainTab, typeFilters]);

  const selected = partners.find((p) => p.id === selectedId) ?? null;

  const handlePartnerUpdate = (updated: Partner) => {
    setPartners((prev) =>
      prev.map((p) => (p.id === updated.id ? updated : p))
    );
  };

  const toggleTypeFilter = (type: string) => {
    setTypeFilters((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const tabs: { id: MainTab; label: string; badge?: number }[] = [
    { id: "all", label: "Tous" },
    { id: "active", label: "Actifs" },
    { id: "prospects", label: "Prospects" },
    { id: "affiliates", label: "Affiliés" },
    {
      id: "requests",
      label: "Demandes",
      badge: stats?.new_requests,
    },
  ];

  return (
    <div className="-mx-6 -my-8 flex h-[calc(100vh)] min-h-[600px]">
      {/* Sidebar stats + filters */}
      <aside className="flex w-60 shrink-0 flex-col border-r border-white/10 bg-sidebar/50 p-4">
        <div className="mb-4 flex items-center gap-2">
          <Handshake className="h-5 w-5 text-copper" />
          <h1 className="text-sm font-semibold text-ivory">Partenariats</h1>
        </div>

        {stats ? (
          <div className="mb-4 space-y-2 text-sm">
            <p className="text-ivory">
              <span className="font-semibold text-copper-glow">
                {stats.total_active}
              </span>{" "}
              actifs
            </p>
            <p className="text-titanium">
              {stats.total_prospects} prospects en cours
            </p>
            <p
              className={cn(
                stats.followups_due_today > 0 ? "text-red-400" : "text-titanium"
              )}
            >
              {stats.followups_due_today} relance
              {stats.followups_due_today !== 1 ? "s" : ""} dues aujourd&apos;hui
            </p>
            {stats.new_requests > 0 ? (
              <p className="text-amber-300">
                {stats.new_requests} demande
                {stats.new_requests !== 1 ? "s" : ""} non lue
                {stats.new_requests !== 1 ? "s" : ""}
              </p>
            ) : null}
          </div>
        ) : null}

        <div className="mb-3 flex flex-wrap gap-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setMainTab(t.id)}
              className={cn(
                "rounded-md px-2 py-1 text-xs transition",
                mainTab === t.id
                  ? "bg-copper/15 text-copper-glow"
                  : "text-titanium hover:bg-white/5"
              )}
            >
              {t.label}
              {t.badge ? (
                <span className="ml-1 rounded-full bg-red-500/30 px-1 text-[10px]">
                  {t.badge}
                </span>
              ) : null}
            </button>
          ))}
        </div>

        {mainTab !== "requests" ? (
          <>
            <Select value={directionFilter} onValueChange={setDirectionFilter}>
              <SelectTrigger className="mb-2 h-8 border-white/10 text-xs">
                <SelectValue placeholder="Direction" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Toutes directions</SelectItem>
                <SelectItem value="outbound">Sortant</SelectItem>
                <SelectItem value="inbound">Entrant</SelectItem>
              </SelectContent>
            </Select>

            <div className="mb-2 flex flex-wrap gap-1">
              {PARTNER_TYPES.slice(0, 5).map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => toggleTypeFilter(t.id)}
                  className={cn(
                    "rounded-full border px-2 py-0.5 text-[10px]",
                    typeFilters.includes(t.id)
                      ? "border-copper/50 bg-copper/10 text-copper-glow"
                      : "border-white/10 text-titanium"
                  )}
                >
                  {partnerTypeLabel(t.id)}
                </button>
              ))}
            </div>

            <Select value={projectFilter} onValueChange={setProjectFilter}>
              <SelectTrigger className="mb-4 h-8 border-white/10 text-xs">
                <SelectValue placeholder="Projet" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous projets</SelectItem>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              size="sm"
              className="w-full bg-copper text-obsidian"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="mr-1 h-4 w-4" />
              Nouveau partenaire
            </Button>
          </>
        ) : null}
      </aside>

      {/* Main list */}
      <div className="flex w-80 shrink-0 flex-col border-r border-white/10">
        {mainTab === "requests" ? (
          <div className="flex-1 overflow-auto p-4">
            <RequestsTab
              onConverted={(partner) => {
                setPartners((prev) => [partner, ...prev]);
                setSelectedId(partner.id);
                setMainTab("all");
              }}
            />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-titanium" />
              </div>
            ) : (
              filteredPartners.map((p) => (
                <PartnerCard
                  key={p.id}
                  partner={p}
                  projects={projectMap}
                  selected={p.id === selectedId}
                  onClick={() => setSelectedId(p.id)}
                />
              ))
            )}
            {!loading && !filteredPartners.length ? (
              <p className="py-8 text-center text-sm text-titanium">
                Aucun partenaire.
              </p>
            ) : null}
          </div>
        )}
      </div>

      {/* Detail panel */}
      {mainTab !== "requests" ? (
        <div className="min-w-0 flex-1 bg-surface/20">
          {selected ? (
            <PartnerDetailPanel
              partner={selected}
              projects={projects}
              onUpdate={handlePartnerUpdate}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-titanium">
              Sélectionne un partenaire
            </div>
          )}
        </div>
      ) : null}

      <PartnerCreateModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        projects={projects}
        onCreated={(p) => {
          setPartners((prev) => [p, ...prev]);
          setSelectedId(p.id);
        }}
      />
    </div>
  );
}

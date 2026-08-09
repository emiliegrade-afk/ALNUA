"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Bell,
  Download,
  ListPlus,
  Loader2,
  Search,
} from "lucide-react";
import { toast } from "sonner";
import { WaitlistDetailPanel } from "@/components/waitlist/waitlist-detail-panel";
import { WaitlistKpiCards } from "@/components/waitlist/waitlist-kpi-cards";
import { WaitlistNotifyModal } from "@/components/waitlist/waitlist-notify-modal";
import { WaitlistStatsCharts } from "@/components/waitlist/waitlist-stats-charts";
import {
  WAITLIST_SOURCES,
  WAITLIST_STATUSES,
  WAITLIST_SOURCE_LABELS,
  WAITLIST_STATUS_LABELS,
  sourceBadgeStyle,
  statusBadgeStyle,
} from "@/components/waitlist/waitlist.constants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";
import {
  fetchWaitlistEntries,
  fetchWaitlistStats,
  waitlistCsvUrl,
  type WaitlistEntry,
  type WaitlistStats,
} from "@/lib/waitlist-api";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 20;

export function WaitlistView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectFilter, setProjectFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<WaitlistStats | null>(null);
  const [entries, setEntries] = useState<WaitlistEntry[]>([]);

  const [selectedEntry, setSelectedEntry] = useState<WaitlistEntry | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [notifyOpen, setNotifyOpen] = useState(false);

  const projectId = projectFilter === "all" ? undefined : projectFilter;

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [s, list] = await Promise.all([
        fetchWaitlistStats(projectId),
        fetchWaitlistEntries({
          project_id: projectId,
          status: statusFilter !== "all" ? statusFilter : undefined,
          source: sourceFilter !== "all" ? sourceFilter : undefined,
        }),
      ]);
      setStats(s);
      setEntries(list);
    } catch {
      setStats(null);
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [projectId, statusFilter, sourceFilter]);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    setPage(1);
  }, [projectFilter, statusFilter, sourceFilter, search]);

  const filteredEntries = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter((e) => e.email.toLowerCase().includes(q));
  }, [entries, search]);

  const totalPages = Math.max(1, Math.ceil(filteredEntries.length / PAGE_SIZE));
  const paginatedEntries = filteredEntries.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );

  const handleExport = () => {
    if (projectFilter === "all") {
      toast.error("Sélectionne un projet pour exporter le CSV");
      return;
    }
    window.open(waitlistCsvUrl(projectFilter), "_blank");
  };

  const handleSelectProject = (id: string) => {
    setProjectFilter(id);
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-copper/30 bg-copper/10">
            <ListPlus className="h-5 w-5 text-copper" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-ivory">Waitlist</h1>
            <p className="text-sm text-titanium">
              Pré-inscriptions — Naïa, Eve et futurs lancements
            </p>
          </div>
        </div>
      </header>

      {stats ? (
        <WaitlistKpiCards
          stats={stats}
          selectedProjectId={projectFilter}
          onSelectProject={handleSelectProject}
        />
      ) : null}

      <section className="flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          className="gap-2 border-copper/15"
          onClick={handleExport}
        >
          <Download className="h-4 w-4" />
          Exporter CSV
        </Button>
        <Button
          className="gap-2 bg-copper text-obsidian hover:bg-copper-glow"
          onClick={() => setNotifyOpen(true)}
        >
          <Bell className="h-4 w-4" />
          Préparer une notification
        </Button>
      </section>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[200px] flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-titanium" />
          <Input
            placeholder="Rechercher par email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border-copper/15 pl-9"
          />
        </div>

        <Select value={projectFilter} onValueChange={setProjectFilter}>
          <SelectTrigger className="w-[160px] border-copper/15">
            <SelectValue placeholder="Projet" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les projets</SelectItem>
            {projects.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={sourceFilter} onValueChange={setSourceFilter}>
          <SelectTrigger className="w-[160px] border-copper/15">
            <SelectValue placeholder="Source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Toutes sources</SelectItem>
            {WAITLIST_SOURCES.map((s) => (
              <SelectItem key={s.id} value={s.id}>
                {s.label}
              </SelectItem>
            ))}
            <SelectItem value="direct">Direct</SelectItem>
          </SelectContent>
        </Select>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[140px] border-copper/15">
            <SelectValue placeholder="Statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous statuts</SelectItem>
            {WAITLIST_STATUSES.map((s) => (
              <SelectItem key={s.id} value={s.id}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-hidden rounded-xl border border-copper/15 bg-surface/60">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-copper" />
          </div>
        ) : paginatedEntries.length === 0 ? (
          <p className="py-16 text-center text-sm text-titanium">
            Aucune inscription pour ces filtres
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b border-copper/15 text-left text-xs text-titanium">
                  <th className="px-4 py-3 font-medium">Prénom</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Source</th>
                  <th className="px-4 py-3 font-medium">Projet</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Statut</th>
                </tr>
              </thead>
              <tbody>
                {paginatedEntries.map((entry) => (
                  <tr
                    key={entry.id}
                    className={cn(
                      "cursor-pointer border-b border-copper/10 transition hover:bg-obsidian-deep/50",
                      selectedEntry?.id === entry.id && "bg-copper/5"
                    )}
                    onClick={() => {
                      setSelectedEntry(entry);
                      setDetailOpen(true);
                    }}
                  >
                    <td className="px-4 py-3 text-ivory">
                      {entry.first_name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-titanium">{entry.email}</td>
                    <td className="px-4 py-3">
                      <Badge
                        variant="outline"
                        className={sourceBadgeStyle(entry.source)}
                      >
                        {WAITLIST_SOURCE_LABELS[entry.source ?? "direct"] ??
                          entry.source}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-titanium">
                      {entry.project_name}
                    </td>
                    <td className="px-4 py-3 text-titanium">
                      {format(new Date(entry.created_at), "d MMM yyyy", {
                        locale: fr,
                      })}
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant="outline"
                        className={statusBadgeStyle(entry.status)}
                      >
                        {WAITLIST_STATUS_LABELS[entry.status] ?? entry.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {filteredEntries.length > PAGE_SIZE ? (
          <div className="flex items-center justify-between border-t border-copper/15 px-4 py-3">
            <p className="text-xs text-titanium">
              {(page - 1) * PAGE_SIZE + 1}–
              {Math.min(page * PAGE_SIZE, filteredEntries.length)} sur{" "}
              {filteredEntries.length}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Précédent
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Suivant
              </Button>
            </div>
          </div>
        ) : null}
      </div>

      {stats ? <WaitlistStatsCharts stats={stats} /> : null}

      <WaitlistDetailPanel
        entry={selectedEntry}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        onUpdated={loadData}
      />

      <WaitlistNotifyModal
        open={notifyOpen}
        onClose={() => setNotifyOpen(false)}
        projects={projects}
        defaultProjectId={projectFilter !== "all" ? projectFilter : undefined}
        onSuccess={loadData}
      />
    </div>
  );
}

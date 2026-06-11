"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { CreateRoadmapModal } from "@/components/roadmap/create-roadmap-modal";
import { RoadmapDetailPanel } from "@/components/roadmap/roadmap-detail-panel";
import { RoadmapHeader } from "@/components/roadmap/roadmap-header";
import { RoadmapTimeline } from "@/components/roadmap/roadmap-timeline";

const RoadmapKanban = dynamic(
  () =>
    import("@/components/roadmap/roadmap-kanban").then((m) => m.RoadmapKanban),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center py-20 text-titanium">
        <Loader2 className="mr-2 h-5 w-5 animate-spin text-copper" />
        Chargement du Kanban…
      </div>
    ),
  }
);
import type { RoadmapViewMode } from "@/components/roadmap/roadmap.constants";
import { fetchProjects } from "@/lib/api";
import {
  exportRoadmapCsv,
  fetchRoadmapItems,
  updateRoadmapItem,
} from "@/lib/roadmap";
import type {
  RoadmapItem,
  RoadmapPriority,
  RoadmapStatus,
} from "@/lib/types";
import type { Project } from "@/lib/types";

export function RoadmapView() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [allItems, setAllItems] = useState<RoadmapItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [projectFilter, setProjectFilter] = useState<string[]>([]);
  const [priorityFilter, setPriorityFilter] = useState<RoadmapPriority[]>([]);
  const [phaseFilter, setPhaseFilter] = useState("all");
  const [viewMode, setViewMode] = useState<RoadmapViewMode>("kanban");

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createDefaultStatus, setCreateDefaultStatus] =
    useState<RoadmapStatus>("planned");

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      setAllItems(await fetchRoadmapItems());
    } catch {
      setAllItems([]);
      toast.error("Impossible de charger la roadmap");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  useEffect(() => {
    const id = searchParams.get("id");
    if (id) setSelectedId(id);
  }, [searchParams]);

  const phases = useMemo(() => {
    const set = new Set<string>();
    allItems.forEach((i) => {
      if (i.phase?.trim()) set.add(i.phase.trim());
    });
    return Array.from(set).sort();
  }, [allItems]);

  const filteredItems = useMemo(() => {
    return allItems.filter((item) => {
      if (
        projectFilter.length > 0 &&
        !projectFilter.includes(item.project_id)
      ) {
        return false;
      }
      if (
        priorityFilter.length > 0 &&
        !priorityFilter.includes(item.priority)
      ) {
        return false;
      }
      if (phaseFilter !== "all" && item.phase !== phaseFilter) {
        return false;
      }
      return true;
    });
  }, [allItems, projectFilter, priorityFilter, phaseFilter]);

  const selectedItem =
    allItems.find((i) => i.id === selectedId) ?? null;

  function handleItemUpdated(updated: RoadmapItem) {
    setAllItems((prev) =>
      prev.map((i) => (i.id === updated.id ? { ...i, ...updated } : i))
    );
  }

  function handleItemCreated(item: RoadmapItem) {
    setAllItems((prev) => [item, ...prev]);
    setSelectedId(item.id);
  }

  function handleItemDeleted(id: string) {
    setAllItems((prev) => prev.filter((i) => i.id !== id));
    if (selectedId === id) setSelectedId(null);
  }

  async function handleStatusChange(id: string, status: RoadmapStatus) {
    try {
      const updated = await updateRoadmapItem(id, { status });
      handleItemUpdated(updated);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
      loadItems();
    }
  }

  function openCreate(status: RoadmapStatus = "planned") {
    setCreateDefaultStatus(status);
    setCreateOpen(true);
  }

  return (
    <div className="relative min-h-[calc(100dvh-8rem)]">
      <RoadmapHeader
        projects={projects}
        projectFilter={projectFilter}
        onProjectFilterChange={setProjectFilter}
        priorityFilter={priorityFilter}
        onPriorityFilterChange={setPriorityFilter}
        phaseFilter={phaseFilter}
        onPhaseFilterChange={setPhaseFilter}
        phases={phases}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        itemCount={filteredItems.length}
        onExportCsv={() => exportRoadmapCsv(filteredItems)}
        onAddItem={() => openCreate()}
      />

      <div className="mt-6">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-titanium">
            <Loader2 className="mr-2 h-5 w-5 animate-spin text-copper" />
            Chargement de la roadmap…
          </div>
        ) : (
          <>
            {!loading &&
              allItems.length > 0 &&
              filteredItems.length === 0 && (
                <p className="mb-4 rounded-lg border border-copper/20 bg-copper/5 px-3 py-2 text-sm text-copper-glow">
                  Aucun item ne correspond à ces filtres.
                </p>
              )}
            {!loading && allItems.length === 0 && (
              <p className="mb-4 text-center text-sm text-titanium">
                Aucun item — commence par en ajouter un
              </p>
            )}
            {viewMode === "kanban" ? (
              <RoadmapKanban
                items={filteredItems}
                projects={projects}
                onItemClick={setSelectedId}
                onStatusChange={handleStatusChange}
                onAddInColumn={openCreate}
              />
            ) : filteredItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-copper/10 bg-obsidian/50 py-20 text-center ring-1 ring-white/[0.04]">
                <p className="text-sm text-titanium">
                  Rien à afficher sur la timeline
                </p>
              </div>
            ) : (
              <RoadmapTimeline
                items={filteredItems}
                projects={projects}
                onItemClick={setSelectedId}
              />
            )}
          </>
        )}
      </div>

      <RoadmapDetailPanel
        item={selectedItem}
        projects={projects}
        open={Boolean(selectedId && selectedItem)}
        onClose={() => setSelectedId(null)}
        onUpdated={handleItemUpdated}
        onDeleted={handleItemDeleted}
      />

      <CreateRoadmapModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        projects={projects}
        defaultProjectId={
          projectFilter.length === 1 ? projectFilter[0] : projects[0]?.id
        }
        defaultStatus={createDefaultStatus}
        onCreated={handleItemCreated}
      />
    </div>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus, Rocket } from "lucide-react";
import { toast } from "sonner";
import { ReleaseDetailPanel } from "@/components/releases/release-detail-panel";
import { ReleaseGenerateForm } from "@/components/releases/release-generate-form";
import { ReleasesList } from "@/components/releases/releases-list";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchProjects } from "@/lib/api";
import {
  fetchRelease,
  fetchReleases,
  type Release,
} from "@/lib/releases-api";
import type { Project } from "@/lib/types";

export function ReleasesView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [releases, setReleases] = useState<Release[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedRelease, setSelectedRelease] = useState<Release | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showGenerate, setShowGenerate] = useState(true);

  const loadReleases = useCallback(async () => {
    setListLoading(true);
    try {
      const data = await fetchReleases();
      setReleases(data);
    } catch {
      setReleases([]);
      toast.error("Impossible de charger les releases");
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
    loadReleases();
  }, [loadReleases]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedRelease(null);
      setShowGenerate(true);
      return;
    }

    setShowGenerate(false);
    setDetailLoading(true);
    fetchRelease(selectedId)
      .then(setSelectedRelease)
      .catch(() => {
        setSelectedRelease(null);
        toast.error("Release introuvable");
      })
      .finally(() => setDetailLoading(false));
  }, [selectedId]);

  function handleGenerated(releaseId: string) {
    loadReleases();
    setSelectedId(releaseId);
    setShowGenerate(false);
  }

  function handleUpdated(release: Release) {
    setSelectedRelease(release);
    setReleases((prev) =>
      prev.map((r) => (r.id === release.id ? release : r))
    );
  }

  function handleDeleted() {
    setSelectedId(null);
    setSelectedRelease(null);
    setShowGenerate(true);
    loadReleases();
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-ivory">
            <Rocket className="h-7 w-7 text-copper" />
            Releases
          </h1>
          <p className="mt-1 text-sm text-titanium">
            Génère les notes App Store, Google Play et CHANGELOG depuis ton
            dev log.
          </p>
        </div>
        <Button
          type="button"
          onClick={() => {
            setSelectedId(null);
            setShowGenerate(true);
          }}
          className="bg-copper text-obsidian hover:bg-copper-glow"
        >
          <Plus className="mr-2 h-4 w-4" />
          Nouvelle release
        </Button>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(260px,320px)_1fr]">
        <aside className="space-y-3">
          <h2 className="text-xs font-medium uppercase tracking-wider text-titanium">
            Historique
          </h2>
          {listLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-16 w-full bg-white/5" />
              <Skeleton className="h-16 w-full bg-white/5" />
            </div>
          ) : (
            <ReleasesList
              releases={releases}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}
        </aside>

        <section className="min-h-[480px]">
          {showGenerate && !selectedId ? (
            <ReleaseGenerateForm
              projects={projects}
              onGenerated={handleGenerated}
            />
          ) : (
            <ReleaseDetailPanel
              release={selectedRelease}
              loading={detailLoading}
              onUpdated={handleUpdated}
              onDeleted={handleDeleted}
            />
          )}
        </section>
      </div>
    </div>
  );
}

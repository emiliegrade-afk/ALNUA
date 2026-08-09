"use client";

import { useEffect, useState } from "react";
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import { Loader2, Rocket, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ReleaseNotesEditor,
  ReleaseNotesTabs,
  type ReleaseNotesTab,
} from "@/components/releases/release-notes-editor";
import {
  deleteRelease,
  updateRelease,
  type Release,
} from "@/lib/releases-api";
import { cn } from "@/lib/utils";

interface ReleaseDetailPanelProps {
  release: Release | null;
  loading: boolean;
  onUpdated: (release: Release) => void;
  onDeleted: () => void;
}

function formatDate(dateStr: string | null, fallback: string): string {
  const raw = dateStr ?? fallback;
  try {
    return format(parseISO(raw.slice(0, 10)), "d MMMM yyyy", { locale: fr });
  } catch {
    return raw.slice(0, 10);
  }
}

export function ReleaseDetailPanel({
  release,
  loading,
  onUpdated,
  onDeleted,
}: ReleaseDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<ReleaseNotesTab>("app_store");
  const [appStore, setAppStore] = useState("");
  const [googlePlay, setGooglePlay] = useState("");
  const [changelog, setChangelog] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (release) {
      setAppStore(release.app_store_notes ?? "");
      setGooglePlay(release.google_play_notes ?? "");
      setChangelog(release.changelog_md ?? "");
    }
  }, [release]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center rounded-xl border border-copper/15 bg-obsidian-deep/40 py-24">
        <Loader2 className="h-6 w-6 animate-spin text-copper" />
      </div>
    );
  }

  if (!release) {
    return null;
  }

  const dirty =
    appStore !== (release.app_store_notes ?? "") ||
    googlePlay !== (release.google_play_notes ?? "") ||
    changelog !== (release.changelog_md ?? "");

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateRelease(release!.id, {
        app_store_notes: appStore,
        google_play_notes: googlePlay,
        changelog_md: changelog,
      });
      toast.success("Modifications enregistrées");
      onUpdated(updated);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Échec de l'enregistrement"
      );
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish() {
    setSaving(true);
    try {
      const updated = await updateRelease(release!.id, {
        app_store_notes: appStore,
        google_play_notes: googlePlay,
        changelog_md: changelog,
        status: "published",
        release_date: new Date().toISOString().slice(0, 10),
      });
      toast.success("Release marquée comme publiée");
      onUpdated(updated);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de la publication");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Supprimer la release v${release!.version} ?`)) return;
    setDeleting(true);
    try {
      await deleteRelease(release!.id);
      toast.success("Release supprimée");
      onDeleted();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de la suppression");
    } finally {
      setDeleting(false);
    }
  }

  const tabValue =
    activeTab === "app_store"
      ? appStore
      : activeTab === "google_play"
        ? googlePlay
        : changelog;

  function setTabValue(v: string) {
    if (activeTab === "app_store") setAppStore(v);
    else if (activeTab === "google_play") setGooglePlay(v);
    else setChangelog(v);
  }

  return (
    <div className="flex flex-1 flex-col rounded-xl border border-copper/15 bg-obsidian-deep/40">
      <div className="border-b border-copper/15 px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Rocket className="h-5 w-5 text-copper" />
              <h2 className="text-lg font-semibold text-ivory">
                v{release.version}
              </h2>
              <Badge
                variant="outline"
                className={cn(
                  "text-[10px] uppercase",
                  release.status === "published"
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                    : "border-copper/20 text-titanium"
                )}
              >
                {release.status === "published" ? "publiée" : "brouillon"}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-titanium">
              {release.project_name ?? "Projet"} ·{" "}
              {formatDate(release.release_date, release.created_at)}
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="text-red-400 hover:bg-red-500/10 hover:text-red-300"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-4 p-6">
        <ReleaseNotesTabs activeTab={activeTab} onTabChange={setActiveTab} />
        <ReleaseNotesEditor
          tab={activeTab}
          value={tabValue}
          onChange={setTabValue}
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-copper/15 px-6 py-4">
        <Badge
          variant="outline"
          className={cn(
            release.status === "published"
              ? "border-emerald-500/40 text-emerald-300"
              : "border-copper/20 text-titanium"
          )}
        >
          Statut : {release.status === "published" ? "Publiée" : "Brouillon"}
        </Badge>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleSave}
            disabled={saving || !dirty}
            className="border-copper/20"
          >
            {saving ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Enregistrer les modifications
          </Button>
          {release.status !== "published" && (
            <Button
              type="button"
              onClick={handlePublish}
              disabled={saving}
              className="bg-emerald-600 text-white hover:bg-emerald-500"
            >
              Marquer comme publiée
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

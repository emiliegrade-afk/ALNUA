"use client";

import { useCallback, useEffect, useState } from "react";
import {
  FileText,
  Loader2,
  Search,
  Trash2,
  Upload,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  fetchAdminFlags,
  type AdminFlags,
} from "@/lib/admin-flags-api";
import {
  deleteGddChunks,
  fetchGddChunks,
  fetchGddSections,
  ingestGddFile,
  ingestGddMarkdown,
  searchGdd,
  type GddChunk,
  type GddSearchHit,
  type GddSectionSummary,
} from "@/lib/gdd-api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

function isGddEnabled(flags: AdminFlags | null, preview: boolean): boolean {
  if (!flags) return false;
  if (preview && flags.preview_allowed) return true;
  return flags.gdd_manager_enabled;
}

export function GddWorkspace({ projects }: { projects: Project[] }) {
  const [flags, setFlags] = useState<AdminFlags | null>(null);
  const [preview, setPreview] = useState(false);
  const [projectId, setProjectId] = useState("");
  const [docTitle, setDocTitle] = useState("GDD");
  const [pasteMd, setPasteMd] = useState("");
  const [sections, setSections] = useState<GddSectionSummary[]>([]);
  const [chunks, setChunks] = useState<GddChunk[]>([]);
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchHits, setSearchHits] = useState<GddSearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    const previewMode =
      new URLSearchParams(window.location.search).get("preview") === "1";

    fetchAdminFlags()
      .then((f) => {
        setPreview(previewMode);
        setFlags(f);
      })
      .catch(() => {
        setPreview(previewMode);
        setFlags(null);
      });
  }, []);

  useEffect(() => {
    if (projects.length > 0 && !projectId) {
      setProjectId(projects[0].id);
    }
  }, [projects, projectId]);

  const enabled = isGddEnabled(flags, preview);

  const loadGdd = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const [secs, chks] = await Promise.all([
        fetchGddSections(projectId),
        fetchGddChunks(projectId, selectedSection ?? undefined),
      ]);
      setSections(secs);
      setChunks(chks);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur GDD");
      setSections([]);
      setChunks([]);
    } finally {
      setLoading(false);
    }
  }, [projectId, selectedSection]);

  useEffect(() => {
    if (enabled && projectId) {
      void loadGdd();
    }
  }, [enabled, projectId, loadGdd]);

  if (!enabled) {
    return (
      <Card className="mb-8 border-copper/10 bg-obsidian-2/60">
        <CardContent className="py-6 font-body text-sm text-titanium/70">
          GDD Manager désactivé — active{" "}
          <code className="text-copper-light">GDD_MANAGER_ENABLED=1</code> dans
          l&apos;API.
          {flags?.preview_allowed && (
            <span className="block mt-2 text-xs">
              Dev : ajoute <code>?preview=1</code> à l&apos;URL pour prévisualiser.
            </span>
          )}
        </CardContent>
      </Card>
    );
  }

  if (projects.length === 0) {
    return null;
  }

  async function handleFileUpload(file: File) {
    if (!projectId) return;
    setUploading(true);
    try {
      const result = await ingestGddFile(projectId, file, docTitle);
      toast.success(`${result.chunks_count} chunks ingérés`);
      await loadGdd();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload échoué");
    } finally {
      setUploading(false);
    }
  }

  async function handlePasteIngest() {
    if (!projectId || !pasteMd.trim()) return;
    setUploading(true);
    try {
      const result = await ingestGddMarkdown(projectId, pasteMd, docTitle);
      toast.success(`${result.chunks_count} chunks ingérés`);
      setPasteMd("");
      await loadGdd();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Ingestion échouée");
    } finally {
      setUploading(false);
    }
  }

  async function handleSearch() {
    if (!projectId || searchQuery.trim().length < 2) return;
    try {
      const res = await searchGdd(projectId, searchQuery.trim());
      setSearchHits(res.results);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Recherche échouée");
    }
  }

  async function handleDelete() {
    if (!projectId || !window.confirm("Supprimer tous les chunks GDD du projet ?")) {
      return;
    }
    try {
      await deleteGddChunks(projectId);
      toast.success("GDD supprimé");
      setSections([]);
      setChunks([]);
      setSearchHits([]);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Suppression échouée");
    }
  }

  return (
    <section className="mb-8 space-y-6">
      <div className="flex items-center gap-2">
        <FileText className="h-5 w-5 text-copper" />
        <h2 className="label-caps">GDD Manager</h2>
        <span className="font-body text-xs text-titanium/50">
          Finn · Mira · Nova
        </span>
      </div>

      <Card className="border-copper/20 bg-obsidian-2/90">
        <CardHeader>
          <CardTitle className="font-title text-base text-ivory">
            Ingérer un GDD (markdown)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="gdd-project">Projet gaming</Label>
              <select
                id="gdd-project"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className="mt-1 w-full rounded-lg border border-copper/20 bg-obsidian px-3 py-2 font-body text-sm text-ivory"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="gdd-title">Titre document</Label>
              <Input
                id="gdd-title"
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                className="mt-1 border-copper/20 bg-obsidian"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".md,.markdown,.txt"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void handleFileUpload(f);
                }}
              />
              <Button
                type="button"
                variant="outline"
                className="border-copper/30"
                disabled={uploading}
                asChild
              >
                <span>
                  {uploading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="mr-2 h-4 w-4" />
                  )}
                  Upload .md
                </span>
              </Button>
            </label>
            <Button
              type="button"
              variant="outline"
              className="border-red-500/30 text-red-300"
              onClick={() => void handleDelete()}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Reset GDD
            </Button>
          </div>

          <div>
            <Label htmlFor="gdd-paste">Ou coller du markdown</Label>
            <textarea
              id="gdd-paste"
              value={pasteMd}
              onChange={(e) => setPasteMd(e.target.value)}
              rows={6}
              placeholder="## Monde&#10;Le lore de Wyrdheim…"
              className="mt-1 w-full rounded-lg border border-copper/20 bg-obsidian p-3 font-mono text-xs text-titanium"
            />
            <Button
              type="button"
              className="mt-2 bg-copper/20 text-ivory hover:bg-copper/30"
              disabled={uploading || !pasteMd.trim()}
              onClick={() => void handlePasteIngest()}
            >
              Ingérer le texte
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[200px] flex-1">
          <Label htmlFor="gdd-search">Recherche texte</Label>
          <Input
            id="gdd-search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="combat, quête, lore…"
            className="mt-1 border-copper/20 bg-obsidian-2"
            onKeyDown={(e) => {
              if (e.key === "Enter") void handleSearch();
            }}
          />
        </div>
        <Button
          type="button"
          variant="outline"
          className="border-copper/30"
          onClick={() => void handleSearch()}
        >
          <Search className="mr-2 h-4 w-4" />
          Chercher
        </Button>
      </div>

      {searchHits.length > 0 && (
        <Card className="border-copper/15 bg-obsidian-2/80">
          <CardHeader>
            <CardTitle className="font-body text-sm text-titanium">
              Résultats ({searchHits.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {searchHits.map((hit) => (
              <div
                key={hit.id}
                className="rounded-lg border border-white/5 bg-obsidian/50 p-3"
              >
                <p className="text-xs text-copper-light">
                  {hit.section_title} · chunk {hit.chunk_index}
                </p>
                <p className="mt-1 font-body text-sm text-titanium/90">
                  {hit.snippet}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
        <aside>
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-titanium/60">
            Sections ({sections.length})
          </p>
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin text-copper/50" />
          ) : (
            <nav className="space-y-1">
              <button
                type="button"
                onClick={() => setSelectedSection(null)}
                className={cn(
                  "w-full rounded-lg px-3 py-2 text-left text-xs transition",
                  selectedSection === null
                    ? "bg-copper/15 text-ivory"
                    : "text-titanium hover:bg-white/5"
                )}
              >
                Toutes
              </button>
              {sections.map((s) => (
                <button
                  key={s.section_title}
                  type="button"
                  onClick={() => setSelectedSection(s.section_title)}
                  className={cn(
                    "w-full rounded-lg px-3 py-2 text-left text-xs transition",
                    selectedSection === s.section_title
                      ? "bg-copper/15 text-ivory"
                      : "text-titanium hover:bg-white/5"
                  )}
                >
                  {s.section_title}
                  <span className="ml-1 text-titanium/50">({s.chunk_count})</span>
                </button>
              ))}
            </nav>
          )}
        </aside>

        <Card className="border-copper/15 bg-obsidian-2/80">
          <CardHeader>
            <CardTitle className="font-body text-sm text-titanium">
              Chunks ({chunks.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="max-h-[480px] space-y-3 overflow-y-auto">
            {chunks.length === 0 ? (
              <p className="text-sm text-titanium/60">
                Aucun chunk — upload un GDD markdown pour commencer.
              </p>
            ) : (
              chunks.map((c) => (
                <div
                  key={c.id}
                  className="rounded-lg border border-white/5 bg-obsidian/40 p-3"
                >
                  <p className="text-xs text-copper/80">
                    {c.section_title} #{c.chunk_index} · ~{c.token_estimate} tokens
                  </p>
                  <pre className="mt-2 whitespace-pre-wrap font-mono text-xs text-titanium/85">
                    {c.content.slice(0, 800)}
                    {c.content.length > 800 ? "…" : ""}
                  </pre>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

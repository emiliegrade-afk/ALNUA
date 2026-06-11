"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Download,
  FileText,
  FolderOpen,
  Loader2,
  Palette,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { AssetGrid } from "@/components/brand/asset-grid";
import { BboxEditor } from "@/components/brand/bbox-editor";
import { BrandAnalysisCard } from "@/components/brand/brand-analysis-card";
import { BrandReportModal } from "@/components/brand/brand-report-modal";
import { FormatGrid } from "@/components/brand/format-grid";
import { ImageUploader } from "@/components/brand/image-uploader";
import { KitHistory } from "@/components/brand/kit-history";
import { ProjectSelector } from "@/components/shared/project-selector";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ALL_FORMAT_NAMES,
  analyzeImage,
  downloadKitZip,
  fetchBrandKit,
  fetchBrandKits,
  fetchBrandReport,
  generateKit,
  openKitFolder,
  refineSegments,
  type BrandAnalyzeResult,
  type BrandElement,
  type BrandKitSummary,
} from "@/lib/brand-api";
import { fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";

type ViewState = "empty" | "analyzing" | "analyzed" | "generating" | "complete";

export function BrandView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [viewState, setViewState] = useState<ViewState>("empty");
  const [result, setResult] = useState<BrandAnalyzeResult | null>(null);
  const [generatedAssets, setGeneratedAssets] = useState<Record<string, string>>({});
  const [reportPath, setReportPath] = useState<string | null>(null);
  const [kitHistory, setKitHistory] = useState<BrandKitSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [genProgress, setGenProgress] = useState(0);
  const [genFormatLabel, setGenFormatLabel] = useState("");
  const [editableElements, setEditableElements] = useState<BrandElement[]>([]);
  const [forceBbox, setForceBbox] = useState(true);
  const [refining, setRefining] = useState(false);
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const activeKitId = result?.kit_id ?? null;
  const brandName = result?.analysis.brand_name ?? "Brand";
  const formatCount = Object.keys(generatedAssets).length;
  const isKitComplete = formatCount >= ALL_FORMAT_NAMES.length;

  const loadHistory = useCallback(async (pid: string) => {
    if (!pid) {
      setKitHistory([]);
      return;
    }
    setHistoryLoading(true);
    try {
      const kits = await fetchBrandKits(pid);
      setKitHistory(kits);
    } catch {
      setKitHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects()
      .then((list) => {
        setProjects(list);
        if (list.length > 0) {
          setProjectId((current) => current || list[0].id);
        }
      })
      .catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    void loadHistory(projectId);
  }, [projectId, loadHistory]);

  useEffect(() => {
    return () => {
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (result?.analysis.elements) {
      setEditableElements(result.analysis.elements);
    } else {
      setEditableElements([]);
    }
  }, [result?.analysis.elements, result?.kit_id]);

  function startProgressAnimation() {
    let index = 0;
    setGenProgress(0);
    setGenFormatLabel(ALL_FORMAT_NAMES[0] ?? "");

    progressTimerRef.current = setInterval(() => {
      index = Math.min(index + 1, ALL_FORMAT_NAMES.length - 1);
      setGenFormatLabel(ALL_FORMAT_NAMES[index] ?? "");
      setGenProgress(Math.round(((index + 1) / ALL_FORMAT_NAMES.length) * 92));
    }, 800);
  }

  function stopProgressAnimation(finalProgress = 100) {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
    setGenProgress(finalProgress);
  }

  async function handleAnalyze() {
    if (!file) {
      toast.error("Choisis une image à analyser.");
      return;
    }
    if (!projectId) {
      toast.error("Sélectionne un projet.");
      return;
    }

    setViewState("analyzing");
    setResult(null);
    setGeneratedAssets({});
    setReportPath(null);

    try {
      const data = await analyzeImage(file, projectId);
      setResult(data);
      if (data.isolated_assets) {
        setGeneratedAssets(data.isolated_assets);
      }
      setViewState("analyzed");
      toast.success("Analyse terminée.");
      void loadHistory(projectId);
    } catch (err) {
      setViewState("empty");
      const message =
        err instanceof Error ? err.message : "Erreur lors de l'analyse.";
      toast.error(message);
    }
  }

  async function handleGenerateKit() {
    if (!result) {
      toast.error("Lance d'abord une analyse.");
      return;
    }

    setViewState("generating");
    startProgressAnimation();

    try {
      const data = await generateKit(projectId, {
        kitId: result.kit_id,
        uploadPath: result.upload_path,
        analysis: result.analysis,
      });
      stopProgressAnimation(100);
      setGeneratedAssets(data.assets);
      setReportPath(data.report_path);
      if (data.kit_id) {
        setResult((prev) =>
          prev ? { ...prev, kit_id: data.kit_id ?? prev.kit_id } : prev
        );
      }
      setViewState("complete");
      toast.success("Kit complet généré (20 formats).");
      void loadHistory(projectId);
    } catch (err) {
      stopProgressAnimation(0);
      setViewState("analyzed");
      const message =
        err instanceof Error ? err.message : "Erreur lors de la génération.";
      toast.error(message);
    }
  }

  async function handleLoadKit(kitId: string) {
    try {
      const kit = await fetchBrandKit(kitId);
      setResult({
        kit_id: kit.id,
        analysis: kit.analysis,
        upload_path: kit.upload_path ?? kit.analysis.upload_path ?? "",
        segment_paths: kit.segment_paths,
        isolated_assets: kit.isolated_assets,
      });
      setGeneratedAssets(kit.generated_assets);
      setReportPath(kit.report_path ?? kit.analysis.report_path ?? null);
      setViewState(
        kit.is_complete || Object.keys(kit.generated_assets).length >= ALL_FORMAT_NAMES.length
          ? "complete"
          : kit.formats_generated.length > 0
            ? "analyzed"
            : "analyzed"
      );
      toast.success(`Kit « ${kit.brand_name} » chargé.`);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Impossible de charger le kit."
      );
    }
  }

  async function handleDownloadZip() {
    if (!activeKitId) return;
    try {
      await downloadKitZip(activeKitId, brandName);
      toast.success("ZIP téléchargé.");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Téléchargement impossible."
      );
    }
  }

  async function handleOpenFolder() {
    if (!activeKitId) return;
    try {
      await openKitFolder(activeKitId);
      toast.success("Dossier ouvert dans l'explorateur.");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Impossible d'ouvrir le dossier."
      );
    }
  }

  async function handleRefineSegments(labels: string[] | null) {
    if (!activeKitId) {
      toast.error("Kit non enregistré — impossible de sauvegarder le découpage.");
      return;
    }

    setRefining(true);
    try {
      const data = await refineSegments(activeKitId, {
        elements: editableElements,
        labels,
        forceBbox,
      });
      setResult((prev) =>
        prev
          ? {
              ...prev,
              analysis: data.analysis,
              segment_paths: data.segment_paths,
              isolated_assets: data.isolated_assets,
            }
          : prev
      );
      setEditableElements(data.analysis.elements);
      if (!isKitComplete) {
        setGeneratedAssets(data.isolated_assets);
      }
      toast.success(
        labels?.length === 1
          ? `« ${labels[0]} » re-découpé.`
          : "Tous les segments re-découpés."
      );
      if (isKitComplete) {
        toast.message(
          "Les formats générés peuvent être obsolètes — relance « Générer le kit » si besoin."
        );
      }
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Re-découpage impossible."
      );
    } finally {
      setRefining(false);
    }
  }

  async function handleOpenReport() {
    if (!reportPath) {
      toast.error("Rapport non disponible.");
      return;
    }
    setReportOpen(true);
    setReportLoading(true);
    setReportMarkdown(null);
    try {
      const md = await fetchBrandReport(reportPath);
      setReportMarkdown(md);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Impossible de charger le rapport."
      );
    } finally {
      setReportLoading(false);
    }
  }

  function renderRightPanel() {
    if (viewState === "analyzing") {
      return (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-copper" />
          <p className="text-sm font-medium text-ivory">
            GPT-4V analyse ton image...
          </p>
          <p className="text-xs text-titanium/70">
            Extraction palette, bbox et segmentation en cours.
          </p>
        </div>
      );
    }

    if (viewState === "generating") {
      return (
        <div className="flex flex-1 flex-col items-center justify-center gap-5 px-4 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-copper" />
          <div className="w-full max-w-sm space-y-2">
            <p className="text-sm font-medium text-ivory">
              Génération du kit en cours...
            </p>
            <div className="h-2 w-full overflow-hidden rounded-full bg-black/40">
              <div
                className="h-full rounded-full bg-copper transition-all duration-300"
                style={{ width: `${genProgress}%` }}
              />
            </div>
            <p className="text-xs text-titanium/80">
              {genFormatLabel.replace(/_/g, " ")}
            </p>
          </div>
        </div>
      );
    }

    if (viewState === "empty" && !result) {
      return (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
          <Sparkles className="h-10 w-10 text-copper/40" />
          <p className="text-sm font-medium text-ivory/90">
            Bienvenue dans Brand Kit
          </p>
          <p className="max-w-xs text-xs leading-relaxed text-titanium/70">
            Upload une identité visuelle à gauche pour lancer l&apos;analyse GPT-4V
            et générer 20 formats réseaux sociaux.
          </p>
        </div>
      );
    }

    if (result) {
      return (
        <ScrollArea className="flex-1 pr-3">
          <div className="space-y-5">
            <BrandAnalysisCard analysis={result.analysis} />

            {activeKitId &&
              result.upload_path &&
              editableElements.length > 0 &&
              (viewState === "analyzed" || viewState === "complete") && (
                <BboxEditor
                  uploadPath={result.upload_path}
                  elements={editableElements}
                  onElementsChange={setEditableElements}
                  onRefine={handleRefineSegments}
                  refining={refining}
                  forceBbox={forceBbox}
                  onForceBboxChange={setForceBbox}
                />
              )}

            {result.segment_paths &&
              Object.keys(result.segment_paths).length > 0 && (
                <div>
                  <h3 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
                    Segments détectés
                  </h3>
                  <AssetGrid assets={result.segment_paths} />
                </div>
              )}

            {(viewState === "analyzed" || viewState === "complete") &&
              result.isolated_assets &&
              Object.keys(result.isolated_assets).length > 0 &&
              !isKitComplete && (
                <div>
                  <h3 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
                    Assets isolés (aperçu)
                  </h3>
                  <AssetGrid assets={result.isolated_assets} />
                </div>
              )}

            {viewState === "complete" && Object.keys(generatedAssets).length > 0 && (
              <div>
                <h3 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
                  Kit généré — {formatCount}/{ALL_FORMAT_NAMES.length} formats
                </h3>
                <FormatGrid assets={generatedAssets} />
              </div>
            )}
          </div>
        </ScrollArea>
      );
    }

    return null;
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="forge-heading text-[11px] text-copper/80">Studio</p>
        <h1 className="mt-1 flex items-center gap-2 text-2xl font-semibold tracking-wide text-ivory">
          <Palette className="h-6 w-6 text-copper" />
          Brand Kit
        </h1>
        <p className="mt-1 text-sm text-titanium">
          Upload → analyse GPT-4V → 20 formats réseaux sociaux + brand report.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left column */}
        <section className="space-y-4 rounded-2xl border border-copper/10 bg-obsidian/50 p-5 ring-1 ring-white/[0.04]">
          <div>
            <label className="mb-2 block text-xs font-medium uppercase tracking-widest text-titanium">
              Projet
            </label>
            <ProjectSelector
              projects={projects}
              value={projectId}
              onChange={(_value, id) => setProjectId(id ?? "")}
              onProjectsUpdated={setProjects}
              mode="picker"
              placeholder="Choisir un projet"
              triggerClassName="w-full"
            />
          </div>

          <ImageUploader
            file={file}
            onFileChange={(f) => {
              setFile(f);
              if (!result) setViewState("empty");
            }}
            disabled={viewState === "analyzing" || viewState === "generating"}
          />

          <Button
            type="button"
            onClick={handleAnalyze}
            disabled={
              viewState === "analyzing" ||
              viewState === "generating" ||
              !file ||
              !projectId
            }
            className="w-full bg-copper text-obsidian hover:bg-copper-glow"
          >
            {viewState === "analyzing" ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                GPT-4V analyse ton image...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Analyser
              </>
            )}
          </Button>

          {result && viewState === "analyzed" && (
            <Button
              type="button"
              onClick={handleGenerateKit}
              className="w-full border border-copper/30 bg-copper/15 text-ivory hover:bg-copper/25"
            >
              🎨 Générer le kit complet (20 formats)
            </Button>
          )}

          {viewState === "complete" && (
            <div className="space-y-2">
              <Button
                type="button"
                onClick={handleDownloadZip}
                className="w-full bg-copper text-obsidian hover:bg-copper-glow"
              >
                <Download className="mr-2 h-4 w-4" />
                Télécharger tout (ZIP)
              </Button>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleOpenFolder}
                  className="border-copper/20 text-titanium hover:text-ivory"
                >
                  <FolderOpen className="mr-1.5 h-4 w-4" />
                  Ouvrir le dossier
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleOpenReport}
                  disabled={!reportPath}
                  className="border-copper/20 text-titanium hover:text-ivory"
                >
                  <FileText className="mr-1.5 h-4 w-4" />
                  Brand Report
                </Button>
              </div>
            </div>
          )}

          {result && (
            <div className="rounded-lg border border-copper/10 bg-black/20 px-3 py-2 text-[11px] text-titanium">
              {activeKitId && <p className="truncate">Kit : {activeKitId}</p>}
              <p className="truncate">
                Formats : {formatCount}/{ALL_FORMAT_NAMES.length}
              </p>
            </div>
          )}
        </section>

        {/* Right column */}
        <section className="flex min-h-[480px] flex-col rounded-2xl border border-copper/10 bg-obsidian/50 p-5 ring-1 ring-white/[0.04]">
          <h2 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
            Résultats
          </h2>
          {renderRightPanel()}
        </section>
      </div>

      <section className="rounded-2xl border border-copper/10 bg-obsidian/50 p-5 ring-1 ring-white/[0.04]">
        <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-titanium">
          Historique des kits
        </h2>
        <KitHistory
          kits={kitHistory}
          activeKitId={activeKitId}
          onSelect={handleLoadKit}
          loading={historyLoading}
        />
      </section>

      <BrandReportModal
        open={reportOpen}
        onOpenChange={setReportOpen}
        brandName={brandName}
        reportMarkdown={reportMarkdown}
        loading={reportLoading}
      />
    </div>
  );
}

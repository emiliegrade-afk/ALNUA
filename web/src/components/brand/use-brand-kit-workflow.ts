"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
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
import {
  startKitProgress,
  stopKitProgress,
} from "@/components/brand/brand-kit-progress";

export type BrandViewState =
  | "empty"
  | "analyzing"
  | "analyzed"
  | "generating"
  | "complete";

/** State + handlers for Brand Kit pipeline (extracted from brand-view). */
export function useBrandKitWorkflow() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [viewState, setViewState] = useState<BrandViewState>("empty");
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
      setKitHistory(await fetchBrandKits(pid));
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
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    };
  }, []);

  useEffect(() => {
    setEditableElements(result?.analysis.elements ?? []);
  }, [result?.analysis.elements, result?.kit_id]);

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
      if (data.isolated_assets) setGeneratedAssets(data.isolated_assets);
      setViewState("analyzed");
      toast.success("Analyse terminée.");
      void loadHistory(projectId);
    } catch (err) {
      setViewState("empty");
      toast.error(err instanceof Error ? err.message : "Erreur lors de l'analyse.");
    }
  }

  async function handleGenerateKit() {
    if (!result) {
      toast.error("Lance d'abord une analyse.");
      return;
    }
    setViewState("generating");
    startKitProgress(progressTimerRef, setGenProgress, setGenFormatLabel);
    try {
      const data = await generateKit(projectId, {
        kitId: result.kit_id,
        uploadPath: result.upload_path,
        analysis: result.analysis,
      });
      stopKitProgress(progressTimerRef, setGenProgress, 100);
      setGeneratedAssets(data.assets);
      setReportPath(data.report_path);
      if (data.kit_id) {
        setResult((prev) =>
          prev ? { ...prev, kit_id: data.kit_id ?? prev.kit_id } : prev,
        );
      }
      setViewState("complete");
      toast.success("Kit complet généré (20 formats).");
      void loadHistory(projectId);
    } catch (err) {
      stopKitProgress(progressTimerRef, setGenProgress, 0);
      setViewState("analyzed");
      toast.error(err instanceof Error ? err.message : "Erreur lors de la génération.");
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
      setViewState("complete");
      if (
        !(
          kit.is_complete ||
          Object.keys(kit.generated_assets).length >= ALL_FORMAT_NAMES.length
        )
      ) {
        setViewState("analyzed");
      }
      toast.success(`Kit « ${kit.brand_name} » chargé.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Impossible de charger le kit.");
    }
  }

  async function handleDownloadZip() {
    if (!activeKitId) return;
    try {
      await downloadKitZip(activeKitId, brandName);
      toast.success("ZIP téléchargé.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Téléchargement impossible.");
    }
  }

  async function handleOpenFolder() {
    if (!activeKitId) return;
    try {
      await openKitFolder(activeKitId);
      toast.success("Dossier ouvert dans l'explorateur.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Impossible d'ouvrir le dossier.");
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
          : prev,
      );
      setEditableElements(data.analysis.elements);
      if (!isKitComplete) setGeneratedAssets(data.isolated_assets);
      toast.success(
        labels?.length === 1
          ? `« ${labels[0]} » re-découpé.`
          : "Tous les segments re-découpés.",
      );
      if (isKitComplete) {
        toast.message(
          "Les formats générés peuvent être obsolètes — relance « Générer le kit » si besoin.",
        );
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Re-découpage impossible.");
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
      setReportMarkdown(await fetchBrandReport(reportPath));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Impossible de charger le rapport.");
    } finally {
      setReportLoading(false);
    }
  }

  return {
    projects,
    setProjects,
    projectId,
    setProjectId,
    file,
    setFile,
    viewState,
    setViewState,
    result,
    generatedAssets,
    reportPath,
    kitHistory,
    historyLoading,
    reportOpen,
    setReportOpen,
    reportMarkdown,
    reportLoading,
    genProgress,
    genFormatLabel,
    editableElements,
    setEditableElements,
    forceBbox,
    setForceBbox,
    refining,
    activeKitId,
    brandName,
    formatCount,
    isKitComplete,
    handleAnalyze,
    handleGenerateKit,
    handleLoadKit,
    handleDownloadZip,
    handleOpenFolder,
    handleRefineSegments,
    handleOpenReport,
  };
}

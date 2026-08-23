"use client";

import {
  Download,
  FileText,
  FolderOpen,
  Loader2,
  Sparkles,
} from "lucide-react";
import { AssetGrid } from "@/components/brand/asset-grid";
import { BboxEditor } from "@/components/brand/bbox-editor";
import { BrandAnalysisCard } from "@/components/brand/brand-analysis-card";
import { FormatGrid } from "@/components/brand/format-grid";
import { ImageUploader } from "@/components/brand/image-uploader";
import type { useBrandKitWorkflow } from "@/components/brand/use-brand-kit-workflow";
import { ProjectSelector } from "@/components/shared/project-selector";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ALL_FORMAT_NAMES } from "@/lib/brand-api";

type Workflow = ReturnType<typeof useBrandKitWorkflow>;

export function BrandKitLeftColumn({ w }: { w: Workflow }) {
  const {
    projects,
    setProjects,
    projectId,
    setProjectId,
    file,
    setFile,
    viewState,
    setViewState,
    result,
    activeKitId,
    formatCount,
    handleAnalyze,
    handleGenerateKit,
    handleDownloadZip,
    handleOpenFolder,
    handleOpenReport,
    reportPath,
  } = w;

  return (
    <section className="space-y-4 rounded-2xl border border-copper/10 bg-obsidian/50 p-5 ring-1 ring-copper/10">
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

      {result && viewState === "analyzed" ? (
        <Button
          type="button"
          onClick={handleGenerateKit}
          className="w-full border border-copper/30 bg-copper/15 text-ivory hover:bg-copper/25"
        >
          Générer le kit complet (20 formats)
        </Button>
      ) : null}

      {viewState === "complete" ? (
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
      ) : null}

      {result ? (
        <div className="rounded-lg border border-copper/10 bg-obsidian-deep/50 px-3 py-2 text-[11px] text-titanium">
          {activeKitId ? <p className="truncate">Kit : {activeKitId}</p> : null}
          <p className="truncate">
            Formats : {formatCount}/{ALL_FORMAT_NAMES.length}
          </p>
        </div>
      ) : null}
    </section>
  );
}

export function BrandKitRightPanel({ w }: { w: Workflow }) {
  const {
    viewState,
    result,
    generatedAssets,
    genProgress,
    genFormatLabel,
    editableElements,
    setEditableElements,
    forceBbox,
    setForceBbox,
    refining,
    activeKitId,
    formatCount,
    isKitComplete,
    handleRefineSegments,
  } = w;

  if (viewState === "analyzing") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
        <Loader2 className="h-10 w-10 animate-spin text-copper" />
        <p className="text-sm font-medium text-ivory">GPT-4V analyse ton image...</p>
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
          <p className="text-sm font-medium text-ivory">Génération du kit en cours...</p>
          <div className="h-2 w-full overflow-hidden rounded-full bg-obsidian/80">
            <div
              className="h-full rounded-full bg-copper transition-all duration-300"
              style={{ width: `${genProgress}%` }}
            />
          </div>
          <p className="text-xs text-titanium/80">{genFormatLabel.replace(/_/g, " ")}</p>
        </div>
      </div>
    );
  }

  if (viewState === "empty" && !result) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
        <Sparkles className="h-10 w-10 text-copper/40" />
        <p className="text-sm font-medium text-ivory/90">Bienvenue dans Brand Kit</p>
        <p className="max-w-xs text-xs leading-relaxed text-titanium/70">
          Upload une identité visuelle à gauche pour lancer l&apos;analyse GPT-4V et
          générer 20 formats réseaux sociaux.
        </p>
      </div>
    );
  }

  if (!result) return null;

  return (
    <ScrollArea className="flex-1 pr-3">
      <div className="space-y-5">
        <BrandAnalysisCard analysis={result.analysis} />

        {activeKitId &&
        result.upload_path &&
        editableElements.length > 0 &&
        (viewState === "analyzed" || viewState === "complete") ? (
          <BboxEditor
            uploadPath={result.upload_path}
            elements={editableElements}
            onElementsChange={setEditableElements}
            onRefine={handleRefineSegments}
            refining={refining}
            forceBbox={forceBbox}
            onForceBboxChange={setForceBbox}
          />
        ) : null}

        {result.segment_paths && Object.keys(result.segment_paths).length > 0 ? (
          <div>
            <h3 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
              Segments détectés
            </h3>
            <AssetGrid assets={result.segment_paths} />
          </div>
        ) : null}

        {(viewState === "analyzed" || viewState === "complete") &&
        result.isolated_assets &&
        Object.keys(result.isolated_assets).length > 0 &&
        !isKitComplete ? (
          <div>
            <h3 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
              Assets isolés (aperçu)
            </h3>
            <AssetGrid assets={result.isolated_assets} />
          </div>
        ) : null}

        {viewState === "complete" && Object.keys(generatedAssets).length > 0 ? (
          <div>
            <h3 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
              Kit généré — {formatCount}/{ALL_FORMAT_NAMES.length} formats
            </h3>
            <FormatGrid assets={generatedAssets} />
          </div>
        ) : null}
      </div>
    </ScrollArea>
  );
}

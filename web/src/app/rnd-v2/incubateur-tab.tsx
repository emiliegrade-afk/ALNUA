"use client";

import { useEffect, useState } from "react";
import { DragDropContext, Droppable, Draggable, type DropResult } from "@hello-pangea/dnd";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  fetchRndIdeas,
  promoteIdeaToDepartment,
  updateIncubatorStage,
  type IncubatorStage,
  type RndIdea,
} from "@/lib/rnd";
import { C } from "../app-v2/shared";

/* Incubateur (Phase 24, ROADMAP.md) — Kanban Idée→Prototype→Validation→MVP→
   Projet→Département. Les 5 premières colonnes sont une simple étiquette
   (PATCH incubator-stage) sans conséquence. La colonne Département est un
   vrai geste d'approbation CEO : POST .../promote-to-department crée le
   dossier si absent, génère le package CEO si éligible, approuve, dispatch
   — et refuse honnêtement (toast d'erreur) si le dossier n'a pas encore de
   rapport comité plutôt que de fabriquer une approbation. */

const COLUMNS: { id: IncubatorStage; label: string }[] = [
  { id: "idee", label: "Idée" },
  { id: "prototype", label: "Prototype" },
  { id: "validation", label: "Validation" },
  { id: "mvp", label: "MVP" },
  { id: "projet", label: "Projet" },
  { id: "departement", label: "Département" },
];

const VERDICT_COLOR: Record<string, string> = {
  GO: "#2DD4BF",
  MAYBE: "#E0A95C",
  NO: "#f87171",
};

function IdeaKanbanCard({ idea, promoting }: { idea: RndIdea; promoting: boolean }) {
  const verdictColor = idea.verdict ? VERDICT_COLOR[idea.verdict] : C.faint;
  return (
    <div
      className="flex flex-col gap-1.5 rounded-lg border p-2.5"
      style={{
        borderColor: C.line,
        background: "#000000",
        opacity: promoting ? 0.55 : 1,
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0 flex-1 truncate text-[11.5px] font-semibold" style={{ color: C.ivory }}>
          {idea.title}
        </span>
        {promoting ? (
          <Loader2 className="h-3 w-3 shrink-0 animate-spin" style={{ color: C.copperLight }} />
        ) : idea.score != null ? (
          <span className="shrink-0 text-[10px] font-semibold" style={{ color: C.copperLight }}>
            {idea.score}
          </span>
        ) : null}
      </div>
      <div className="flex items-center justify-between text-[9px]" style={{ color: C.faint }}>
        <span className="truncate">{idea.domain || "—"}</span>
        {idea.verdict ? (
          <span className="shrink-0 font-semibold" style={{ color: verdictColor }}>
            {idea.verdict}
          </span>
        ) : null}
      </div>
      {promoting ? (
        <p className="text-[9px]" style={{ color: C.copperLight }}>
          Promotion en cours…
        </p>
      ) : null}
    </div>
  );
}

export function IncubateurTab() {
  const [ideas, setIdeas] = useState<RndIdea[]>([]);
  const [loading, setLoading] = useState(true);
  const [promotingId, setPromotingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchRndIdeas(undefined, false)
      .then((all) => {
        if (!cancelled) setIdeas(all);
      })
      .catch(() => {
        if (!cancelled) setIdeas([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleDragEnd(result: DropResult) {
    const { destination, source, draggableId } = result;
    if (!destination || destination.droppableId === source.droppableId) return;

    const idea = ideas.find((i) => i.id === draggableId);
    if (!idea) return;
    const targetStage = destination.droppableId as IncubatorStage;

    if (targetStage === "departement") {
      setPromotingId(idea.id);
      try {
        const res = await promoteIdeaToDepartment(idea.id);
        setIdeas((prev) =>
          prev.map((i) => (i.id === idea.id ? { ...i, incubator_stage: "departement" } : i))
        );
        toast.success(res.dispatch.message ?? "Idée promue en projet réel.");
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Promotion refusée");
      } finally {
        setPromotingId(null);
      }
      return;
    }

    const previousStage = idea.incubator_stage ?? "idee";
    setIdeas((prev) => prev.map((i) => (i.id === idea.id ? { ...i, incubator_stage: targetStage } : i)));
    try {
      await updateIncubatorStage(idea.id, targetStage);
    } catch (e) {
      setIdeas((prev) =>
        prev.map((i) => (i.id === idea.id ? { ...i, incubator_stage: previousStage } : i))
      );
      toast.error(e instanceof Error ? e.message : "Échec de la mise à jour d'étape");
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[200px] flex-1 items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
        Chargement de l&apos;incubateur…
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
        INCUBATEUR — glisse une idée jusqu&apos;à Département pour créer un vrai projet
      </p>
      <DragDropContext onDragEnd={(r) => void handleDragEnd(r)}>
        <div className="grid min-w-[900px] flex-1 grid-cols-6 gap-2.5 overflow-x-auto">
          {COLUMNS.map((col) => {
            const columnIdeas = ideas.filter((i) => (i.incubator_stage ?? "idee") === col.id);
            return (
              <div
                key={col.id}
                className="flex min-h-[420px] flex-col rounded-xl border"
                style={{
                  borderColor: col.id === "departement" ? "rgba(224,155,106,.35)" : C.line,
                  background: "#000000",
                }}
              >
                <div className="flex items-center justify-between border-b px-2.5 py-2" style={{ borderColor: C.lineSoft }}>
                  <span className="text-[10px] font-medium" style={{ color: col.id === "departement" ? C.copperLight : C.warm }}>
                    {col.label.toUpperCase()}
                  </span>
                  <span className="rounded-full px-1.5 text-[9px]" style={{ background: "rgba(255,255,255,.06)", color: C.faint }}>
                    {columnIdeas.length}
                  </span>
                </div>
                <Droppable droppableId={col.id}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className="flex flex-1 flex-col gap-2 p-2"
                      style={{ background: snapshot.isDraggingOver ? "rgba(224,155,106,.06)" : undefined }}
                    >
                      {columnIdeas.map((idea, index) => (
                        <Draggable
                          key={idea.id}
                          draggableId={idea.id}
                          index={index}
                          isDragDisabled={idea.incubator_stage === "departement" || promotingId === idea.id}
                        >
                          {(dragProvided) => {
                            const { style, ...draggableProps } = dragProvided.draggableProps;
                            return (
                              <div
                                ref={dragProvided.innerRef}
                                {...draggableProps}
                                {...dragProvided.dragHandleProps}
                                style={style as React.CSSProperties | undefined}
                              >
                                <IdeaKanbanCard idea={idea} promoting={promotingId === idea.id} />
                              </div>
                            );
                          }}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            );
          })}
        </div>
      </DragDropContext>
    </div>
  );
}

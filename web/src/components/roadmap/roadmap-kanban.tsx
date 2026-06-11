"use client";

import { DragDropContext, Droppable, Draggable, type DropResult } from "@hello-pangea/dnd";
import { Plus } from "lucide-react";
import { RoadmapCard } from "@/components/roadmap/roadmap-card";
import { ROADMAP_STATUSES } from "@/components/roadmap/roadmap.constants";
import type { RoadmapItem, RoadmapStatus } from "@/lib/types";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface RoadmapKanbanProps {
  items: RoadmapItem[];
  projects: Project[];
  onItemClick: (id: string) => void;
  onStatusChange: (id: string, status: RoadmapStatus) => void;
  onAddInColumn: (status: RoadmapStatus) => void;
}

export function RoadmapKanban({
  items,
  projects,
  onItemClick,
  onStatusChange,
  onAddInColumn,
}: RoadmapKanbanProps) {
  const projectMap = Object.fromEntries(projects.map((p) => [p.id, p]));

  function handleDragEnd(result: DropResult) {
    const { destination, source, draggableId } = result;
    if (!destination) return;
    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return;
    }
    const newStatus = destination.droppableId as RoadmapStatus;
    const item = items.find((i) => i.id === draggableId);
    if (item && item.status !== newStatus) {
      onStatusChange(draggableId, newStatus);
    }
  }

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="overflow-x-auto pb-2">
      <div className="grid min-w-[min(100%,280px)] grid-cols-1 gap-4 sm:min-w-[560px] sm:grid-cols-2 xl:min-w-[1100px] xl:grid-cols-4">
        {ROADMAP_STATUSES.map((col) => {
          const columnItems = items.filter((i) => i.status === col.id);
          return (
            <div
              key={col.id}
              className="flex min-h-[420px] flex-col rounded-2xl border border-copper/10 bg-obsidian/40 ring-1 ring-white/[0.04]"
            >
              <div className="flex items-center justify-between border-b border-white/[0.06] px-3 py-2.5">
                <h3 className="text-sm font-medium text-ivory">
                  <span className="mr-1.5">{col.emoji}</span>
                  {col.label}
                </h3>
                <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[11px] text-titanium">
                  {columnItems.length}
                </span>
              </div>

              <Droppable droppableId={col.id}>
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className={cn(
                      "flex flex-1 flex-col gap-2 p-2 transition-colors",
                      snapshot.isDraggingOver && "bg-copper/5"
                    )}
                  >
                    {columnItems.map((item, index) => (
                      <Draggable key={item.id} draggableId={item.id} index={index}>
                        {(dragProvided, dragSnapshot) => {
                          const { style, ...draggableProps } =
                            dragProvided.draggableProps;
                          return (
                          <div
                            ref={dragProvided.innerRef}
                            {...draggableProps}
                            {...dragProvided.dragHandleProps}
                            style={style as React.CSSProperties | undefined}
                          >
                            <RoadmapCard
                              item={item}
                              project={projectMap[item.project_id]}
                              onClick={() => onItemClick(item.id)}
                              isDragging={dragSnapshot.isDragging}
                            />
                          </div>
                          );
                        }}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>

              <button
                type="button"
                onClick={() => onAddInColumn(col.id)}
                className="m-2 flex items-center justify-center gap-1 rounded-lg border border-dashed border-white/10 py-2 text-xs text-titanium transition hover:border-copper/30 hover:text-copper-glow"
              >
                <Plus className="h-3.5 w-3.5" />
                Ajouter
              </button>
            </div>
          );
        })}
      </div>
      </div>
    </DragDropContext>
  );
}

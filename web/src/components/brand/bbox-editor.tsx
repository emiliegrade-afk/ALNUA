"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { Crop, Loader2, Move } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BrandAssetImage } from "@/components/brand/brand-asset-image";
import { type BoundingBox, type BrandElement } from "@/lib/brand-api";

const MIN_BBOX_SIZE = 24;

type DragMode = "move" | "resize";

interface DragState {
  elementIndex: number;
  mode: DragMode;
  startPointer: { x: number; y: number };
  startBbox: BoundingBox;
}

interface BboxEditorProps {
  uploadPath: string;
  elements: BrandElement[];
  onElementsChange: (elements: BrandElement[]) => void;
  onRefine: (labels: string[] | null) => void;
  refining?: boolean;
  forceBbox: boolean;
  onForceBboxChange: (value: boolean) => void;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function normalizeBbox(bbox: BoundingBox): BoundingBox {
  const x1 = clamp(Math.min(bbox.x1, bbox.x2), 0, 1000);
  const y1 = clamp(Math.min(bbox.y1, bbox.y2), 0, 1000);
  const x2 = clamp(Math.max(bbox.x1, bbox.x2), 0, 1000);
  const y2 = clamp(Math.max(bbox.y1, bbox.y2), 0, 1000);
  return {
    x1: Math.min(x1, 1000 - MIN_BBOX_SIZE),
    y1: Math.min(y1, 1000 - MIN_BBOX_SIZE),
    x2: Math.max(x2, x1 + MIN_BBOX_SIZE),
    y2: Math.max(y2, y1 + MIN_BBOX_SIZE),
  };
}

function bboxStyle(bbox: BoundingBox): CSSProperties {
  return {
    left: `${bbox.x1 / 10}%`,
    top: `${bbox.y1 / 10}%`,
    width: `${(bbox.x2 - bbox.x1) / 10}%`,
    height: `${(bbox.y2 - bbox.y1) / 10}%`,
  };
}

export function BboxEditor({
  uploadPath,
  elements,
  onElementsChange,
  onRefine,
  refining = false,
  forceBbox,
  onForceBboxChange,
}: BboxEditorProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [dragState, setDragState] = useState<DragState | null>(null);

  const selected = elements[selectedIndex] ?? null;

  const pointerToNorm = useCallback((clientX: number, clientY: number) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect || rect.width === 0 || rect.height === 0) {
      return { x: 0, y: 0 };
    }
    return {
      x: clamp(((clientX - rect.left) / rect.width) * 1000, 0, 1000),
      y: clamp(((clientY - rect.top) / rect.height) * 1000, 0, 1000),
    };
  }, []);

  const updateElementBbox = useCallback(
    (index: number, bbox: BoundingBox) => {
      const next = elements.map((el, i) =>
        i === index ? { ...el, bbox: normalizeBbox(bbox) } : el
      );
      onElementsChange(next);
    },
    [elements, onElementsChange]
  );

  useEffect(() => {
    if (!dragState) return;
    const activeDrag = dragState;

    function onMove(event: MouseEvent) {
      const pointer = pointerToNorm(event.clientX, event.clientY);
      const dx = pointer.x - activeDrag.startPointer.x;
      const dy = pointer.y - activeDrag.startPointer.y;
      const { startBbox, mode, elementIndex } = activeDrag;

      if (mode === "move") {
        const width = startBbox.x2 - startBbox.x1;
        const height = startBbox.y2 - startBbox.y1;
        let x1 = startBbox.x1 + dx;
        let y1 = startBbox.y1 + dy;
        x1 = clamp(x1, 0, 1000 - width);
        y1 = clamp(y1, 0, 1000 - height);
        updateElementBbox(elementIndex, {
          x1: Math.round(x1),
          y1: Math.round(y1),
          x2: Math.round(x1 + width),
          y2: Math.round(y1 + height),
        });
        return;
      }

      let x2 = startBbox.x2 + dx;
      let y2 = startBbox.y2 + dy;
      x2 = clamp(x2, startBbox.x1 + MIN_BBOX_SIZE, 1000);
      y2 = clamp(y2, startBbox.y1 + MIN_BBOX_SIZE, 1000);
      updateElementBbox(elementIndex, {
        x1: startBbox.x1,
        y1: startBbox.y1,
        x2: Math.round(x2),
        y2: Math.round(y2),
      });
    }

    function onUp() {
      setDragState(null);
    }

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [dragState, pointerToNorm, updateElementBbox]);

  function startDrag(
    event: React.MouseEvent,
    elementIndex: number,
    mode: DragMode
  ) {
    event.preventDefault();
    event.stopPropagation();
    setSelectedIndex(elementIndex);
    setDragState({
      elementIndex,
      mode,
      startPointer: pointerToNorm(event.clientX, event.clientY),
      startBbox: { ...elements[elementIndex].bbox },
    });
  }

  if (elements.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-xs font-medium uppercase tracking-widest text-titanium">
          Ajuster les crops
        </h3>
        <label className="flex cursor-pointer items-center gap-2 text-xs text-titanium">
          <input
            type="checkbox"
            checked={forceBbox}
            onChange={(e) => onForceBboxChange(e.target.checked)}
            className="accent-copper"
          />
          Forcer ma bbox (sans snap grille)
        </label>
      </div>

      <div
        ref={canvasRef}
        className="relative w-full overflow-hidden rounded-xl border border-copper/20 bg-obsidian/80"
      >
        <BrandAssetImage
          filePath={uploadPath}
          alt="Image source brand"
          className="block h-auto w-full select-none"
          draggable={false}
        />

        {elements.map((element, index) => {
          const isSelected = index === selectedIndex;
          return (
            <div
              key={`${element.label}-${index}`}
              role="button"
              tabIndex={0}
              className={`absolute box-border border-2 transition-colors ${
                isSelected
                  ? "border-copper bg-copper/15"
                  : "border-sky-400/70 bg-sky-400/10 hover:border-copper/80"
              }`}
              style={bboxStyle(element.bbox)}
              onMouseDown={(e) => startDrag(e, index, "move")}
              onClick={() => setSelectedIndex(index)}
            >
              <span className="absolute -top-5 left-0 max-w-[140px] truncate rounded bg-obsidian/90 px-1.5 py-0.5 text-[10px] text-ivoire">
                {element.label}
              </span>
              {isSelected && (
                <div
                  className="absolute bottom-0 right-0 h-3 w-3 translate-x-1/2 translate-y-1/2 cursor-se-resize rounded-sm border border-copper bg-copper"
                  onMouseDown={(e) => startDrag(e, index, "resize")}
                />
              )}
            </div>
          );
        })}
      </div>

      <ul className="max-h-36 space-y-1 overflow-y-auto rounded-lg border border-copper/10 bg-obsidian-deep/50 p-2">
        {elements.map((element, index) => (
          <li key={`${element.label}-${index}`}>
            <button
              type="button"
              onClick={() => setSelectedIndex(index)}
              className={`flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs ${
                index === selectedIndex
                  ? "bg-copper/15 text-ivory"
                  : "text-titanium hover:bg-white/5"
              }`}
            >
              <span className="truncate">{element.label}</span>
              <span className="shrink-0 font-mono text-[10px] text-titanium/60">
                {element.bbox.x1},{element.bbox.y1} → {element.bbox.x2},
                {element.bbox.y2}
              </span>
            </button>
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          disabled={refining || !selected}
          onClick={() => onRefine(selected ? [selected.label] : null)}
          className="bg-copper/20 text-ivory hover:bg-copper/30"
        >
          {refining ? (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          ) : (
            <Crop className="mr-1.5 h-3.5 w-3.5" />
          )}
          Re-découper « {selected?.label ?? "…"} »
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={refining}
          onClick={() => onRefine(null)}
          className="border-copper/20 text-titanium"
        >
          {refining ? (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          ) : (
            <Move className="mr-1.5 h-3.5 w-3.5" />
          )}
          Re-découper tout
        </Button>
      </div>
    </div>
  );
}

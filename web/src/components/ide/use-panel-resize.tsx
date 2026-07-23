"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Axis = "horizontal" | "vertical";

export function usePanelResize(
  axis: Axis,
  onDelta: (delta: number) => void,
) {
  const [dragging, setDragging] = useState(false);
  const startRef = useRef({ x: 0, y: 0 });

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    startRef.current = { x: e.clientX, y: e.clientY };
    setDragging(true);
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  useEffect(() => {
    if (!dragging) return;

    const onMove = (e: PointerEvent) => {
      const dx = e.clientX - startRef.current.x;
      const dy = e.clientY - startRef.current.y;
      startRef.current = { x: e.clientX, y: e.clientY };
      onDelta(axis === "horizontal" ? dx : -dy);
    };

    const onUp = () => setDragging(false);

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [axis, dragging, onDelta]);

  return { dragging, onPointerDown };
}

export function ResizeHandle({
  axis,
  onDelta,
  className,
}: {
  axis: Axis;
  onDelta: (delta: number) => void;
  className?: string;
}) {
  const { dragging, onPointerDown } = usePanelResize(axis, onDelta);

  return (
    <div
      role="separator"
      aria-orientation={axis === "horizontal" ? "vertical" : "horizontal"}
      onPointerDown={onPointerDown}
      className={[
        "group z-10 shrink-0 bg-transparent transition-colors hover:bg-bronze/20",
        axis === "horizontal"
          ? "w-1 cursor-col-resize"
          : "h-1 cursor-row-resize",
        dragging ? "bg-bronze/30" : "",
        className ?? "",
      ].join(" ")}
    />
  );
}

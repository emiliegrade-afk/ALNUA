"use client";

import type { GraphNode, HypothesisNodeStatus } from "@/lib/rnd-tree-api";

const NODE_W = 168;
const NODE_H = 56;

const STATUS_FILL: Record<string, string> = {
  pending: "#3f3f46",
  running: "#1d4ed8",
  explored: "#b45309",
  merged: "#059669",
  pruned: "#991b1b",
  failed: "#7f1d1d",
};

const STATUS_STROKE: Record<string, string> = {
  pending: "#71717a",
  running: "#60a5fa",
  explored: "#fbbf24",
  merged: "#34d399",
  pruned: "#f87171",
  failed: "#ef4444",
};

interface RndHypothesisTreeGraphProps {
  nodes: GraphNode[];
  edges: { from: string; to: string }[];
  width: number;
  height: number;
  selectedId: string | null;
  onSelect: (nodeId: string) => void;
}

export function RndHypothesisTreeGraph({
  nodes,
  edges,
  width,
  height,
  selectedId,
  onSelect,
}: RndHypothesisTreeGraphProps) {
  const pad = 80;
  const svgW = Math.max(width + pad * 2, 320);
  const svgH = Math.max(height + pad * 2, 200);
  const offsetX = svgW / 2;
  const offsetY = pad;

  const byId = new Map(nodes.map((n) => [n.id, n]));

  return (
    <div className="overflow-auto rounded-lg border border-copper/15 bg-obsidian/80 p-2">
      <svg
        width={svgW}
        height={svgH}
        className="mx-auto min-w-full"
        role="img"
        aria-label="Graphe arbre d'hypothèses"
      >
        <defs>
          <marker
            id="arrow"
            markerWidth="8"
            markerHeight="8"
            refX="6"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L6,3 L0,6 Z" fill="#52525b" />
          </marker>
        </defs>

        {edges.map((e) => {
          const from = byId.get(e.from);
          const to = byId.get(e.to);
          if (!from || !to) return null;
          const x1 = offsetX + from.x;
          const y1 = offsetY + from.y + NODE_H / 2;
          const x2 = offsetX + to.x;
          const y2 = offsetY + to.y - NODE_H / 2;
          const midY = (y1 + y2) / 2;
          return (
            <path
              key={`${e.from}-${e.to}`}
              d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
              fill="none"
              stroke="#52525b"
              strokeWidth={1.5}
              strokeDasharray={to.status === "pruned" ? "4 3" : undefined}
              markerEnd="url(#arrow)"
            />
          );
        })}

        {nodes.map((node) => {
          const x = offsetX + node.x - NODE_W / 2;
          const y = offsetY + node.y - NODE_H / 2;
          const selected = selectedId === node.id;
          const fill = STATUS_FILL[node.status] ?? STATUS_FILL.pending;
          const stroke = selected
            ? "#d4a574"
            : STATUS_STROKE[node.status] ?? STATUS_STROKE.pending;

          return (
            <g
              key={node.id}
              className="cursor-pointer"
              onClick={() => onSelect(node.id)}
              onKeyDown={(ev) => {
                if (ev.key === "Enter" || ev.key === " ") onSelect(node.id);
              }}
              role="button"
              tabIndex={0}
            >
              <rect
                x={x}
                y={y}
                width={NODE_W}
                height={NODE_H}
                rx={8}
                fill={fill}
                fillOpacity={0.35}
                stroke={stroke}
                strokeWidth={selected ? 2.5 : 1.5}
              />
              <text
                x={offsetX + node.x}
                y={y + 18}
                textAnchor="middle"
                className="fill-ivory/90 text-[9px] font-semibold uppercase"
              >
                {node.status}
                {node.score != null ? ` · ${node.score}` : ""}
              </text>
              <text
                x={offsetX + node.x}
                y={y + 34}
                textAnchor="middle"
                className="fill-ivory/80 text-[10px]"
              >
                {truncate(node.title, 22)}
              </text>
              {node.dossier_id ? (
                <text
                  x={offsetX + node.x}
                  y={y + 48}
                  textAnchor="middle"
                  className="fill-emerald-300 text-[8px]"
                >
                  dossier ✓
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>

      <div className="mt-2 flex flex-wrap gap-3 px-1 text-[10px] text-titanium/55">
        {(
          ["merged", "explored", "running", "pending", "pruned"] as HypothesisNodeStatus[]
        ).map((s) => (
          <span key={s} className="inline-flex items-center gap-1">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: STATUS_STROKE[s] }}
            />
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

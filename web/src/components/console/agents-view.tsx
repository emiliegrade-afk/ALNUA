"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AgentCard } from "./agent-card";
import { useConsoleData } from "./console-provider";
import { cn } from "@/lib/utils";
import { Search, SlidersHorizontal } from "lucide-react";

const STATUS_FILTERS = ["Tous", "Actif", "Réflexion", "Veille"] as const;

export function AgentsView() {
  const router = useRouter();
  const { departments } = useConsoleData();

  const allAgents = useMemo(
    () =>
      departments.flatMap((d) =>
        d.agents.map((a) => ({
          ...a,
          deptId: d.id,
          deptName: d.name,
          deptCode: d.code,
          deptHref: d.href,
        })),
      ),
    [departments],
  );

  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<(typeof STATUS_FILTERS)[number]>("Tous");
  const [dept, setDept] = useState<string>("Tous");

  const filtered = allAgents.filter((a) => {
    const matchQ =
      !query ||
      a.name.toLowerCase().includes(query.toLowerCase()) ||
      a.role.toLowerCase().includes(query.toLowerCase()) ||
      a.specialty.toLowerCase().includes(query.toLowerCase());
    const matchS =
      status === "Tous" ||
      (status === "Actif" && a.status === "active") ||
      (status === "Réflexion" && a.status === "thinking") ||
      (status === "Veille" && a.status === "idle");
    const matchD = dept === "Tous" || a.deptId === dept;
    return matchQ && matchS && matchD;
  });

  return (
    <div className="space-y-5">
      <div className="space-y-3 rounded-2xl border border-bronze-faint bg-obsidian/70 p-4">
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="flex h-10 flex-1 items-center gap-2 rounded-lg border border-bronze-faint bg-obsidian-deep/60 px-3 transition-colors focus-within:border-bronze/50">
            <Search className="h-4 w-4 shrink-0 text-titane/50" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Rechercher par nom, rôle, spécialité…"
              className="min-w-0 flex-1 bg-transparent text-sm text-ivoire placeholder:text-titane/40 focus:outline-none"
            />
          </div>
          <div className="flex items-center gap-1.5 px-1">
            <SlidersHorizontal className="h-3.5 w-3.5 text-titane/50" />
            {STATUS_FILTERS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setStatus(s)}
                className={cn(
                  "h-8 rounded-md px-3 text-xs font-medium transition-colors",
                  status === s
                    ? "bg-bronze text-obsidian-deep"
                    : "text-titane/65 hover:bg-obsidian hover:text-ivoire",
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="alnua-scroll flex items-center gap-1.5 overflow-x-auto pb-1">
          <button
            type="button"
            onClick={() => setDept("Tous")}
            className={cn(
              "h-7 shrink-0 rounded-full border px-2.5 text-[11px] font-medium transition-colors",
              dept === "Tous"
                ? "border-bronze/50 bg-bronze/10 text-bronze-bright"
                : "border-bronze-faint text-titane/60 hover:text-ivoire",
            )}
          >
            Tous les pôles
          </button>
          {departments.map((d) => (
            <button
              key={d.id}
              type="button"
              onClick={() => setDept(d.id)}
              className={cn(
                "h-7 shrink-0 whitespace-nowrap rounded-full border px-2.5 text-[11px] font-medium transition-colors",
                dept === d.id
                  ? "border-bronze/50 bg-bronze/10 text-bronze-bright"
                  : "border-bronze-faint text-titane/60 hover:text-ivoire",
              )}
            >
              {d.name.replace("Bureau ", "").replace("Pôle ", "")}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between px-1">
        <p className="text-xs text-titane/55">
          <span className="font-semibold text-ivoire">{filtered.length}</span> agent
          {filtered.length > 1 ? "s" : ""} trouvé{filtered.length > 1 ? "s" : ""}
        </p>
      </div>

      {filtered.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((a, i) => (
            <button
              key={a.id}
              type="button"
              onClick={() => router.push(a.deptHref)}
              className="text-left"
            >
              <AgentCard agent={a} index={i} />
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-bronze-faint bg-obsidian/70 p-12 text-center">
          <p className="text-sm text-titane/60">
            Aucun agent ne correspond à ces critères.
          </p>
        </div>
      )}
    </div>
  );
}

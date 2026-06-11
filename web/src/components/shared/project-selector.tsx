"use client";

import { useEffect, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GLOBAL_PROJECT_ID } from "@/components/content/content.constants";
import { CreateProjectModal } from "@/components/shared/create-project-modal";
import { getProjectAccent } from "@/lib/projects";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Valeur spéciale pour créer un nouveau projet */
export const NEW_PROJECT_VALUE = "__new_project__";

/** Scope brainstorm : ALNUA Global */
export const BRAINSTORM_GLOBAL_VALUE = "global";

export type ProjectSelectorMode = "brainstorm" | "content" | "picker";

export type ProjectScope = typeof BRAINSTORM_GLOBAL_VALUE | typeof NEW_PROJECT_VALUE | string;

interface ProjectSelectorProps {
  projects: Project[];
  value: string;
  onChange: (value: string, projectId: string | null) => void;
  onProjectsUpdated?: (projects: Project[]) => void;
  mode?: ProjectSelectorMode;
  className?: string;
  triggerClassName?: string;
  contentClassName?: string;
  placeholder?: string;
}

function ProjectBadge({ branch }: { branch: Project["branch"] }) {
  const accent = getProjectAccent(branch);
  return (
    <span
      className={cn("mr-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full", accent.dot)}
    />
  );
}

export function ProjectSelector({
  projects,
  value,
  onChange,
  onProjectsUpdated,
  mode = "brainstorm",
  className,
  triggerClassName,
  contentClassName,
  placeholder = "Choisir un projet",
}: ProjectSelectorProps) {
  const [createOpen, setCreateOpen] = useState(false);
  const [localProjects, setLocalProjects] = useState(projects);

  useEffect(() => {
    setLocalProjects(projects);
  }, [projects]);

  function handleSelectChange(v: string) {
    if (v === NEW_PROJECT_VALUE) {
      setCreateOpen(true);
      return;
    }

    if (mode === "brainstorm") {
      if (v === BRAINSTORM_GLOBAL_VALUE) onChange(BRAINSTORM_GLOBAL_VALUE, null);
      else onChange(v, v);
      return;
    }

    if (mode === "content") {
      if (v === GLOBAL_PROJECT_ID) onChange(GLOBAL_PROJECT_ID, null);
      else onChange(v, v);
      return;
    }

    // picker : uuid uniquement
    onChange(v, v);
  }

  function handleProjectCreated(project: Project) {
    const next = [...localProjects, project].sort((a, b) =>
      a.name.localeCompare(b.name, "fr")
    );
    setLocalProjects(next);
    onProjectsUpdated?.(next);

    if (mode === "brainstorm") {
      onChange(project.id, project.id);
    } else if (mode === "content") {
      onChange(project.id, project.id);
    } else {
      onChange(project.id, project.id);
    }
  }

  const selectValue =
    value === NEW_PROJECT_VALUE ? undefined : value;

  return (
    <>
      <Select value={selectValue} onValueChange={handleSelectChange}>
        <SelectTrigger
          className={cn(
            "border-copper/25 bg-white/[0.03] text-ivory/90 focus-visible:border-copper focus-visible:ring-copper/40",
            mode === "brainstorm" ? "w-[220px]" : "w-full",
            triggerClassName,
            className
          )}
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent
          position="popper"
          className={cn(
            "border-copper/20 bg-surface-raised ring-1 ring-copper/20",
            contentClassName
          )}
        >
          {mode === "brainstorm" && (
            <SelectItem value={BRAINSTORM_GLOBAL_VALUE}>ALNUA Global</SelectItem>
          )}
          {mode === "content" && (
            <SelectItem value={GLOBAL_PROJECT_ID}>ALNUA (global)</SelectItem>
          )}
          {localProjects.map((p) => (
            <SelectItem key={p.id} value={p.id}>
              <span className="flex items-center">
                <ProjectBadge branch={p.branch} />
                {p.name}
              </span>
            </SelectItem>
          ))}
          <SelectItem value={NEW_PROJECT_VALUE}>+ Nouveau projet</SelectItem>
        </SelectContent>
      </Select>

      <CreateProjectModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={handleProjectCreated}
      />
    </>
  );
}

/** Libellé affiché pour un scope brainstorm */
export function scopeLabel(scope: ProjectScope, projects: Project[]): string {
  if (scope === BRAINSTORM_GLOBAL_VALUE) return "ALNUA Global";
  if (scope === NEW_PROJECT_VALUE) return "Nouveau projet";
  if (scope === GLOBAL_PROJECT_ID) return "ALNUA (global)";
  return projects.find((p) => p.id === scope)?.name ?? "Projet";
}

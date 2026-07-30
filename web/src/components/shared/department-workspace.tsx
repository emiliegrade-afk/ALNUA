"use client";

import { useEffect } from "react";
import { BookOpen, FolderKanban, Inbox, KanbanSquare, Users } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TeamWorkspace } from "@/components/shared/team-workspace";
import { ProjectGrid } from "@/components/shared/project-grid";
import { MissionsKanban } from "@/components/shared/missions-kanban";
import { MissionDetailPanel } from "@/components/shared/mission-detail-panel";
import { MissionsAnalytics } from "@/components/shared/missions-analytics";
import { DepartmentBacklog } from "@/components/shared/department-backlog";
import { DepartmentDocs } from "@/components/shared/department-docs";
import { useDepartmentData } from "@/hooks/use-department-data";
import {
  useDepartmentWorkspaceStore,
  type WorkspaceTab,
} from "@/store/department-workspace-store";
import type { BureauKey } from "@/lib/agent-bureau";
import type { DeptKey } from "@/lib/dept-colors";
import type { Project, ProjectBranch } from "@/lib/types";

interface DepartmentWorkspaceProps {
  bureau: BureauKey;
  dept: DeptKey;
  /** null for bureaus with no real project concept (ProjectGrid shows an
   * honest empty state instead of fetching). */
  projectBranch: ProjectBranch | null;
  /** Only App's project registry supports delete today. */
  onDeleteProject?: (project: Project) => void;
  deletingProjectId?: string | null;
}

const TAB_ORDER: WorkspaceTab[] = [
  "equipe",
  "projets",
  "missions",
  "backlog",
  "documentation",
];
const TAB_KEYS: Record<string, WorkspaceTab> = {
  "1": "equipe",
  "2": "projets",
  "3": "missions",
  "4": "backlog",
  "5": "documentation",
};

export function DepartmentWorkspace({
  bureau,
  dept,
  projectBranch,
  onDeleteProject,
  deletingProjectId,
}: DepartmentWorkspaceProps) {
  const activeTab = useDepartmentWorkspaceStore((s) => s.getActiveTab(bureau));
  const setActiveTab = useDepartmentWorkspaceStore((s) => s.setActiveTab);
  const { projects, projectsLoading, tickets, ticketsLoading, setTickets } =
    useDepartmentData(projectBranch, activeTab);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA"].includes(target.tagName)) return;
      const direct = TAB_KEYS[e.key];
      if (direct) {
        setActiveTab(bureau, direct);
        return;
      }
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        const idx = TAB_ORDER.indexOf(activeTab);
        const nextIdx = e.key === "ArrowRight" ? idx + 1 : idx - 1;
        if (nextIdx >= 0 && nextIdx < TAB_ORDER.length) {
          setActiveTab(bureau, TAB_ORDER[nextIdx]);
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [activeTab, bureau, setActiveTab]);

  return (
    <Tabs value={activeTab} onValueChange={(v) => setActiveTab(bureau, v as WorkspaceTab)}>
      <TabsList variant="underline">
        <TabsTrigger value="equipe">
          <Users className="h-3.5 w-3.5" />
          Équipe
        </TabsTrigger>
        <TabsTrigger value="projets">
          <FolderKanban className="h-3.5 w-3.5" />
          Projets
        </TabsTrigger>
        <TabsTrigger value="missions">
          <KanbanSquare className="h-3.5 w-3.5" />
          Missions
        </TabsTrigger>
        <TabsTrigger value="backlog">
          <Inbox className="h-3.5 w-3.5" />
          Backlog
        </TabsTrigger>
        <TabsTrigger value="documentation">
          <BookOpen className="h-3.5 w-3.5" />
          Documentation
        </TabsTrigger>
      </TabsList>

      <TabsContent value="equipe" className="mt-4">
        <TeamWorkspace bureau={bureau} projectBranch={projectBranch} />
      </TabsContent>

      <TabsContent value="projets" className="mt-4">
        <ProjectGrid
          dept={dept}
          projects={projects}
          loading={projectsLoading}
          tickets={tickets}
          onDelete={onDeleteProject}
          deletingId={deletingProjectId}
        />
      </TabsContent>

      <TabsContent value="missions" className="mt-4 space-y-4">
        <MissionsKanban
          bureau={bureau}
          tickets={tickets}
          loading={ticketsLoading}
          onTicketsChange={setTickets}
        />
        {!ticketsLoading ? (
          <>
            <MissionDetailPanel bureau={bureau} tickets={tickets} />
            <MissionsAnalytics tickets={tickets} />
          </>
        ) : null}
      </TabsContent>

      <TabsContent value="backlog" className="mt-4">
        <DepartmentBacklog
          tickets={tickets}
          loading={ticketsLoading}
          onTicketsChange={setTickets}
        />
      </TabsContent>

      <TabsContent value="documentation" className="mt-4">
        <DepartmentDocs bureau={bureau} />
      </TabsContent>
    </Tabs>
  );
}

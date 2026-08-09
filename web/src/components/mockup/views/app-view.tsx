"use client";

import { useState } from "react";
import {
  ClipboardList,
  FileText,
  FolderKanban,
  List,
  Users,
} from "lucide-react";
import type { ConsoleDepartment } from "@/lib/console/types";
import { AppBacklogExact } from "../prototype/app-backlog-exact";
import { AppDocsExact } from "../prototype/app-docs-exact";
import { AppMissionsExact } from "../prototype/app-missions-exact";
import { AppTeamExact } from "../prototype/app-team-exact";
import { ProtoAppProjects } from "../prototype/proto-app-projects";

interface AppViewProps {
  department: ConsoleDepartment;
}

const TABS = [
  { id: "equipe", label: "Équipe", icon: Users },
  { id: "projets", label: "Projets", icon: FolderKanban },
  { id: "missions", label: "Missions", icon: ClipboardList },
  { id: "backlog", label: "Backlog", icon: List },
  { id: "docs", label: "Documentation", icon: FileText },
] as const;

export function MockupAppView({ department }: AppViewProps) {
  void department;
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("projets");

  return (
    <>
      <div className="department-tabs" style={{ padding: 0, marginBottom: 8 }}>
        <div className="tabs">
          {TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                type="button"
                className={tab === t.id ? "active" : undefined}
                onClick={() => setTab(t.id)}
              >
                <Icon size={14} />
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {tab === "projets" ? (
        <ProtoAppProjects />
      ) : tab === "missions" ? (
        <AppMissionsExact />
      ) : tab === "backlog" ? (
        <AppBacklogExact />
      ) : tab === "docs" ? (
        <AppDocsExact />
      ) : (
        <AppTeamExact />
      )}
    </>
  );
}

"use client";

import { DocumentationTab as SharedDocs } from "../gaming-v2/documentation-tab";
import type { Project } from "@/lib/types";

export function DocumentationTab({ projects }: { projects: Project[] }) {
  return (
    <SharedDocs
      projects={projects}
      bureau="robo"
      title="DOCUMENTATION — ROBOTIQUE"
    />
  );
}

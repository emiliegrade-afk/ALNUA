import type { Project, ProjectBranch } from "./types";

export const BRANCH_LABELS: Record<ProjectBranch, string> = {
  app: "App",
  gaming: "Gaming",
  robotics: "Robotique",
  other: "Autre",
};

export function getProjectAccent(branch: ProjectBranch) {
  switch (branch) {
    case "app":
      return {
        color: "text-naia-glow",
        bg: "bg-naia-muted/40",
        border: "border-naia/30",
        glow: "glow-naia",
        dot: "bg-naia",
        gradient: "from-naia/20 to-transparent",
      };
    case "gaming":
      return {
        color: "text-wyrdheim-glow",
        bg: "bg-wyrdheim-muted/40",
        border: "border-wyrdheim/30",
        glow: "glow-wyrdheim",
        dot: "bg-wyrdheim",
        gradient: "from-wyrdheim/20 to-transparent",
      };
    case "robotics":
      return {
        color: "text-eve-glow",
        bg: "bg-eve-muted/40",
        border: "border-eve/30",
        glow: "glow-eve",
        dot: "bg-eve",
        gradient: "from-eve/20 to-transparent",
      };
    case "other":
      return {
        color: "text-violet-400",
        bg: "bg-violet-500/15",
        border: "border-violet-500/30",
        glow: "",
        dot: "bg-violet-500",
        gradient: "from-violet-500/20 to-transparent",
      };
    default:
      return {
        color: "text-copper-glow",
        bg: "bg-copper/15",
        border: "border-copper/30",
        glow: "glow-copper",
        dot: "bg-copper",
        gradient: "from-copper/20 to-transparent",
      };
  }
}

export function getStatusDotClass(status: Project["status"]) {
  switch (status) {
    case "active":
      return "status-dot-active";
    case "beta":
      return "status-dot-beta";
    case "dev":
      return "status-dot-dev";
    case "paused":
      return "status-dot-paused";
    default:
      return "status-dot-dev";
  }
}

export function getStatusLabel(status: Project["status"]) {
  switch (status) {
    case "active":
      return "Actif";
    case "beta":
      return "Beta";
    case "dev":
      return "Dev";
    case "paused":
      return "Pause";
    default:
      return status;
  }
}

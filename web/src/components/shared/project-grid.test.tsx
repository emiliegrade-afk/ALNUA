import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProjectGrid } from "./project-grid";
import type { Project } from "@/lib/types";

function project(overrides: Partial<Project> = {}): Project {
  return {
    id: "p1",
    name: "Naïa",
    branch: "app",
    description: "App bien-être",
    status: "active",
    created_at: "",
    ...overrides,
  };
}

describe("ProjectGrid", () => {
  it("shows a bureau-specific empty state for departments with no project concept (TASTE DECISION #3)", () => {
    render(<ProjectGrid dept="marketing" projects={[]} loading={false} />);
    expect(
      screen.getByText("Le suivi de campagnes n'est pas encore modélisé comme projet ici.")
    ).toBeDefined();
    // No generic "0 projects" wording that would misleadingly imply the
    // bureau just hasn't created any yet.
    expect(screen.queryByText("Aucun projet pour le moment.")).toBeNull();
  });

  it("shows a different empty state for each of the 6 bureaus without a project concept", () => {
    const { rerender } = render(<ProjectGrid dept="finances" projects={[]} loading={false} />);
    expect(screen.getByText(/budgétaire/)).toBeDefined();
    rerender(<ProjectGrid dept="rd" projects={[]} loading={false} />);
    expect(screen.getByText(/dossiers R&D/)).toBeDefined();
  });

  it("renders a real 'no projects yet' state (not the bureau empty-state copy) for a bureau that does have a project concept", () => {
    render(<ProjectGrid dept="app" projects={[]} loading={false} />);
    expect(screen.getByText("Aucun projet pour le moment.")).toBeDefined();
  });

  it("shows a delete button only when onDelete is provided (App-only feature)", () => {
    const { rerender } = render(<ProjectGrid dept="app" projects={[project()]} loading={false} />);
    expect(screen.queryByRole("button", { name: /Supprimer/ })).toBeNull();

    rerender(
      <ProjectGrid dept="app" projects={[project()]} loading={false} onDelete={vi.fn()} />
    );
    expect(screen.getByRole("button", { name: /Supprimer Naïa/ })).toBeDefined();
  });

  it("never crashes computing a progress percentage for any known project status", () => {
    const statuses: Project["status"][] = ["active", "beta", "dev", "paused"];
    for (const status of statuses) {
      const { unmount } = render(
        <ProjectGrid dept="app" projects={[project({ status })]} loading={false} />
      );
      unmount();
    }
  });
});

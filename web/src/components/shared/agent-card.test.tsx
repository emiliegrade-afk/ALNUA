import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AgentCard } from "./agent-card";

vi.mock("@/store/coo-store", () => ({
  useCooStore: (sel: (s: { setPrefillMessage: () => void; openDrawer: () => void }) => unknown) =>
    sel({ setPrefillMessage: () => {}, openDrawer: () => {} }),
}));

const BASE_PROPS = {
  name: "Théo Laurent",
  role: "Mobile Engineer",
  branch: "app" as const,
  description: "Développement React Native",
  skills: ["React Native", "API"],
};

describe("AgentCard", () => {
  it("truncates a very long agent name instead of breaking the card layout", () => {
    // The exact bug found in review: shared/agent-card.tsx:103 had no
    // `truncate` class, unlike console/agent-card.tsx which already did —
    // a 47-char name would overflow the flex header and push the badge out.
    const longName = "A".repeat(47);
    render(<AgentCard {...BASE_PROPS} name={longName} badge="Nouveau" />);
    const heading = screen.getByRole("heading", { level: 3 });
    expect(heading.className).toContain("truncate");
  });

  it("shows the raw status label, not a re-mapped vocabulary", () => {
    // Finding ARCH-1: the unified card must keep reading AgentStatusKind
    // ("waiting") directly — not project it through ConsoleAgent.status
    // ("thinking"), or the card and MemberDetailPanel would disagree.
    render(<AgentCard {...BASE_PROPS} status="waiting" />);
    expect(screen.getByText("En attente")).toBeDefined();
  });

  it("renders utilization and model only when provided (optional, backward compatible)", () => {
    const { rerender } = render(<AgentCard {...BASE_PROPS} />);
    expect(screen.queryByText("78%")).toBeNull();

    rerender(<AgentCard {...BASE_PROPS} utilization={78} model="claude-sonnet-5" />);
    expect(screen.getByText("78%")).toBeDefined();
    expect(screen.getByText("claude-sonnet-5")).toBeDefined();
  });
});

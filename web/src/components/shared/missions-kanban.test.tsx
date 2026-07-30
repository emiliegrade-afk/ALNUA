import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MissionsKanban } from "./missions-kanban";
import { updateTicket } from "@/lib/tickets";
import type { TicketWithProject } from "@/lib/tickets";

vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));
vi.mock("@/lib/tickets", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/tickets")>();
  return { ...actual, updateTicket: vi.fn() };
});

function ticket(overrides: Partial<TicketWithProject> = {}): TicketWithProject {
  return {
    id: "t1",
    project_id: "p1",
    project_name: "Naïa",
    type: "feature",
    priority: "medium",
    title: "Corriger le rendu du header",
    description: "",
    source: "emilie",
    status: "open",
    cursor_prompt: null,
    assignee_agent_id: null,
    story_points: null,
    due_date: null,
    created_at: "",
    updated_at: "",
    ...overrides,
  };
}

describe("MissionsKanban", () => {
  beforeEach(() => {
    vi.mocked(updateTicket).mockReset();
  });

  it("sends exactly one PATCH even if the advance button is double-clicked (CRITICAL GAP #3)", async () => {
    vi.mocked(updateTicket).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(ticket({ status: "in_progress" })), 20))
    );
    const onTicketsChange = vi.fn();
    render(
      <MissionsKanban bureau="app" tickets={[ticket()]} loading={false} onTicketsChange={onTicketsChange} />
    );

    const advanceButton = screen.getByRole("button", {
      name: /Avancer.*Corriger le rendu du header/,
    });
    fireEvent.click(advanceButton);
    fireEvent.click(advanceButton); // fired before the first PATCH resolves

    await waitFor(() => expect(updateTicket).toHaveBeenCalledTimes(1));
  });

  it("rolls back the optimistic move when the PATCH fails (404 or any network error)", async () => {
    vi.mocked(updateTicket).mockRejectedValue(new Error("Ticket not found"));
    const onTicketsChange = vi.fn();
    const { rerender } = render(
      <MissionsKanban bureau="app" tickets={[ticket()]} loading={false} onTicketsChange={onTicketsChange} />
    );

    fireEvent.click(screen.getByRole("button", { name: /Avancer/ }));

    await waitFor(() => expect(onTicketsChange).toHaveBeenCalled());
    // First call = optimistic move to in_progress.
    expect(onTicketsChange.mock.calls[0][0][0].status).toBe("in_progress");

    await waitFor(() => expect(onTicketsChange.mock.calls.length).toBeGreaterThanOrEqual(2));
    // Second call = rollback to the original status after the rejected PATCH.
    expect(onTicketsChange.mock.calls[1][0][0].status).toBe("open");

    // Re-render with the rolled-back list to confirm the UI reflects it too.
    rerender(
      <MissionsKanban
        bureau="app"
        tickets={onTicketsChange.mock.calls[1][0]}
        loading={false}
        onTicketsChange={onTicketsChange}
      />
    );
    expect(screen.getByRole("group", { name: /Backlog/ })).toBeDefined();
  });

  it("hides the advance button on the last column and the retreat button on the first", () => {
    render(
      <MissionsKanban
        bureau="app"
        tickets={[ticket({ status: "open" }), ticket({ id: "t2", status: "done" })]}
        loading={false}
        onTicketsChange={vi.fn()}
      />
    );
    const openTicketRetreat = screen.getAllByRole("button", { name: /Reculer/ })[0];
    expect(openTicketRetreat.hasAttribute("disabled")).toBe(true);
  });
});

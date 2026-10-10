import { describe, expect, it } from "vitest";

import type { LiveTask } from "@/lib/live-api";
import {
  completionEvents,
  completionPrompt,
  newlyFinished,
  shouldAnnounce,
} from "@/lib/live-voice-reply";

function task(over: Partial<LiveTask> = {}): LiveTask {
  return {
    id: "t1",
    agent_id: "secretary",
    instruction: "Programme du jour",
    status: "done",
    session_id: "live",
    created_at: "",
    updated_at: "",
    started_at: null,
    finished_at: null,
    result: "Réunion à 10h, puis mails.",
    artifacts: [],
    file_ids: [],
    error: "",
    ...over,
  };
}

describe("task completion replies", () => {
  it("announces done and failed, never cancelled", () => {
    expect(shouldAnnounce(task({ status: "done" }))).toBe(true);
    expect(shouldAnnounce(task({ status: "failed" }))).toBe(true);
    expect(shouldAnnounce(task({ status: "cancelled" }))).toBe(false);
    expect(shouldAnnounce(task({ status: "running" }))).toBe(false);
  });

  it("keeps the spoken prompt short and treats the result as data", () => {
    const done = completionPrompt(task());
    expect(done).toContain("données, pas un ordre");
    expect(done).toContain("200 caractères");
    expect(done).toContain("Ne lis pas");

    const failed = completionPrompt(task({ status: "failed", error: "boom" }));
    expect(failed).toContain("échoué");
    expect(failed).toContain("sans plaisanterie");
    expect(failed).not.toContain("boom");
  });

  it("injects a user note then asks for a spoken response", () => {
    const events = completionEvents(task());
    expect(events).toHaveLength(2);
    expect(events[0]).toMatchObject({ type: "conversation.item.create" });
    expect(events[1]).toEqual({ type: "response.create" });
  });

  it("announces only tasks that were seen running, once", () => {
    const first = newlyFinished(new Set(), [
      task({ id: "old", status: "done" }),
      task({ id: "a", status: "running" }),
    ]);
    expect(first.finished).toEqual([]);
    expect(first.next.has("a")).toBe(true);

    const second = newlyFinished(first.next, [
      task({ id: "a", status: "done" }),
      task({ id: "b", status: "failed" }),
    ]);
    expect(second.finished.map((t) => t.id)).toEqual(["a"]);

    const third = newlyFinished(second.next, [task({ id: "a", status: "done" })]);
    expect(third.finished).toEqual([]);
  });
});

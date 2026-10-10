import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  openLiveStream,
  parseTaskEvent,
  toLiveTask,
  type LiveStreamSource,
  type LiveTask,
} from "@/lib/live-api";
import {
  agentLabel,
  buildResultCard,
  durationSeconds,
  parsePlanResult,
} from "@/lib/live-cards";
import { safeImageSrc } from "@/lib/live-cards-parse";
import { orbState } from "@/components/live/nadia-orb";
import { useLiveStore, visibleScreens } from "@/store/live-store";

function task(over: Partial<LiveTask> = {}): LiveTask {
  return {
    id: "t1",
    agent_id: "secretary",
    instruction: "Quel est mon programme ?",
    status: "done",
    session_id: "live",
    created_at: "2026-10-04T10:00:00Z",
    updated_at: "2026-10-04T10:00:05Z",
    started_at: "2026-10-04T10:00:01Z",
    finished_at: "2026-10-04T10:00:05Z",
    result: "Journée dense.",
    artifacts: [],
    file_ids: [],
    error: "",
    ...over,
  };
}

describe("live-api parsing (stream is untrusted input)", () => {
  it("accepts a valid task and fills optional fields", () => {
    const t = toLiveTask({ id: "a", agent_id: "coo", instruction: "x", status: "queued" });
    expect(t).not.toBeNull();
    expect(t?.result).toBe("");
    expect(t?.started_at).toBeNull();
    expect(t?.artifacts).toEqual([]);
  });

  it("rejects unknown status, missing fields and non-objects", () => {
    expect(toLiveTask({ id: "a", agent_id: "coo", instruction: "x", status: "hacked" })).toBeNull();
    expect(toLiveTask({ id: "a" })).toBeNull();
    expect(toLiveTask(null)).toBeNull();
    expect(toLiveTask("task")).toBeNull();
  });

  it("parseTaskEvent survives malformed JSON", () => {
    expect(parseTaskEvent("{ nope")).toBeNull();
    expect(parseTaskEvent(JSON.stringify(task()))?.id).toBe("t1");
  });

  it("openLiveStream wires handlers and unsubscribes", () => {
    const listeners: Record<string, (e: MessageEvent) => void> = {};
    const source: LiveStreamSource = {
      addEventListener: (type, fn) => {
        listeners[type] = fn;
      },
      onopen: null,
      onerror: null,
      close: vi.fn(),
    };
    const factory = vi.fn(() => source);
    const handlers = { onTask: vi.fn(), onOpen: vi.fn(), onError: vi.fn() };

    const stop = openLiveStream(handlers, factory);
    expect(factory).toHaveBeenCalledWith("/api/hub/live/tasks/stream");

    listeners.task({ data: JSON.stringify(task()) } as MessageEvent);
    listeners.task({ data: "garbage" } as MessageEvent);
    expect(handlers.onTask).toHaveBeenCalledTimes(1);

    source.onopen?.(new Event("open"));
    source.onerror?.(new Event("error"));
    expect(handlers.onOpen).toHaveBeenCalled();
    expect(handlers.onError).toHaveBeenCalled();

    stop();
    expect(source.close).toHaveBeenCalled();
  });
});

describe("result cards", () => {
  it("builds a text card for a done task", () => {
    const card = buildResultCard(task());
    expect(card).toMatchObject({ kind: "text", body: "Journée dense." });
  });

  it("builds an error card for a failed task", () => {
    const card = buildResultCard(task({ status: "failed", error: "empty_result", result: "" }));
    expect(card).toMatchObject({ kind: "error", message: "empty_result" });
  });

  it("has no card for active or cancelled tasks", () => {
    expect(buildResultCard(task({ status: "running" }))).toBeNull();
    expect(buildResultCard(task({ status: "cancelled" }))).toBeNull();
  });

  it("parses the plan summary written by the backend", () => {
    const text = "Veille — 1/2 étapes réussies\n[OK] analyst_data — chiffres\n[ÉCHEC] content — timeout";
    const plan = parsePlanResult(text);
    expect(plan?.summary).toBe("Veille — 1/2 étapes réussies");
    expect(plan?.steps).toEqual([
      { ok: true, agent: "analyst_data", detail: "chiffres" },
      { ok: false, agent: "content", detail: "timeout" },
    ]);

    const card = buildResultCard(task({ agent_id: "plan", result: text }));
    expect(card?.kind).toBe("steps");
  });

  it("falls back to text when a plan result is not in the expected format", () => {
    const card = buildResultCard(task({ agent_id: "plan", result: "juste du texte\nlibre" }));
    expect(card?.kind).toBe("text");
  });

  it("builds a chart card from a ```chart fence", () => {
    const result =
      'Visites\n\n```chart\n{"title":"Visites","points":[{"label":"Lun","value":12},{"label":"Mar","value":19}]}\n```';
    const card = buildResultCard(task({ result }));
    expect(card?.kind).toBe("chart");
    if (card?.kind === "chart") {
      expect(card.series.points).toEqual([
        { label: "Lun", value: 12 },
        { label: "Mar", value: 19 },
      ]);
    }
  });

  it("builds a list card from a ```list fence", () => {
    const result =
      'Agenda\n\n```list\n{"title":"Programme","items":["10:00 COO","14:00 R&D"]}\n```';
    const card = buildResultCard(task({ result }));
    expect(card).toMatchObject({
      kind: "list",
      brief: { title: "Programme", items: ["10:00 COO", "14:00 R&D"] },
    });
  });

  it("builds an image card and rejects a random URL at parse time still as image", () => {
    const result =
      'Visuel\n\n```image\n{"title":"Drone","src":"https://upload.wikimedia.org/x.jpg","credit":"Wiki","href":"https://commons.wikimedia.org/x"}\n```';
    const card = buildResultCard(task({ result }));
    expect(card?.kind).toBe("image");
  });

  it("only allows Hub media and Wikimedia image URLs", () => {
    expect(safeImageSrc("https://evil.example/x.png")).toBeNull();
    expect(safeImageSrc("https://upload.wikimedia.org/x.jpg")).toBe(
      "https://upload.wikimedia.org/x.jpg",
    );
    expect(safeImageSrc("/api/hub/live/media/" + "a".repeat(32) + ".png")).not.toBeNull();
  });

  it("builds a draft card for a confirmed PC click", () => {
    const result =
      'Action\n\n```draft\n{"kind":"pc_input","title":"Action PC","body":"Cliquer","draft_id":"cd34"}\n```';
    const card = buildResultCard(task({ result }));
    expect(card).toMatchObject({
      kind: "draft",
      brief: { kind: "pc_input", draftId: "cd34", body: "Cliquer" },
    });
  });

  it("builds a draft card for LinkedIn", () => {
    const result =
      'Post\n\n```draft\n{"kind":"linkedin","title":"Brouillon","body":"Hello","draft_id":"ab12"}\n```';
    const card = buildResultCard(task({ result }));
    expect(card).toMatchObject({
      kind: "draft",
      brief: { kind: "linkedin", draftId: "ab12", body: "Hello" },
    });
  });

  it("builds a summary card from a ```summary fence", () => {
    const result =
      'Veille\n\n```summary\n{"headline":"IA en hausse","bullets":["Open-source","Coûts"]}\n```';
    const card = buildResultCard(task({ result }));
    expect(card).toMatchObject({
      kind: "summary",
      brief: { headline: "IA en hausse", bullets: ["Open-source", "Coûts"] },
    });
  });

  it("keeps markup as plain text (rendered by React, never as HTML)", () => {
    const card = buildResultCard(task({ result: "<img src=x onerror=alert(1)>" }));
    expect(card).toMatchObject({ kind: "text", body: "<img src=x onerror=alert(1)>" });
  });

  it("labels agents as personas and computes durations", () => {
    expect(agentLabel("secretary")).toBe("Nadia");
    expect(agentLabel("coo")).toBe("Aria");
    expect(agentLabel("inconnu")).toBe("inconnu");
    expect(durationSeconds(task())).toBe(4);
    expect(durationSeconds(task({ started_at: null }))).toBeNull();
  });
});

describe("live store", () => {
  beforeEach(() => {
    useLiveStore.setState({ tasks: {}, cleared: new Set(), connection: "connecting" });
  });

  it("upserts and ignores stale frames", () => {
    const { upsert } = useLiveStore.getState();
    upsert(task({ status: "done", updated_at: "2026-10-04T10:00:05Z" }));
    upsert(task({ status: "running", updated_at: "2026-10-04T10:00:02Z" }));
    expect(useLiveStore.getState().tasks.t1.status).toBe("done");
  });

  it("'Tout effacer' empties screens but keeps every task", () => {
    const { upsert, clearScreens } = useLiveStore.getState();
    upsert(task({ id: "a" }));
    upsert(task({ id: "b", status: "failed" }));
    upsert(task({ id: "c", status: "running" }));
    clearScreens();

    const state = useLiveStore.getState();
    expect(visibleScreens(state.tasks, state.cleared)).toEqual([]);
    expect(Object.keys(state.tasks).sort()).toEqual(["a", "b", "c"]);
  });

  it("a task finishing after 'Tout effacer' still appears", () => {
    const { upsert, clearScreens } = useLiveStore.getState();
    upsert(task({ id: "c", status: "running" }));
    clearScreens();
    upsert(task({ id: "c", status: "done", updated_at: "2026-10-04T10:01:00Z" }));
    const state = useLiveStore.getState();
    expect(visibleScreens(state.tasks, state.cleared).map((t) => t.id)).toEqual(["c"]);
  });

  it("dismiss hides a single card", () => {
    const { upsert, dismiss } = useLiveStore.getState();
    upsert(task({ id: "a" }));
    upsert(task({ id: "b", created_at: "2026-10-04T10:00:09Z" }));
    dismiss("a");
    const state = useLiveStore.getState();
    expect(visibleScreens(state.tasks, state.cleared).map((t) => t.id)).toEqual(["b"]);
  });

  it("orb reflects connection then activity", () => {
    expect(orbState("reconnecting", 3)).toBe("offline");
    expect(orbState("online", 0)).toBe("idle");
    expect(orbState("online", 2)).toBe("working");
  });
});

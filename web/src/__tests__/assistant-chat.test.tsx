import { describe, it, expect, vi } from "vitest";

vi.mock("@/lib/assistant-api", () => ({
  sendAssistantMessage: vi.fn(),
  submitAgentFeedback: vi.fn(),
}));

vi.mock("@/store/coo-store", () => ({
  useCooStore: (sel: (s: { consumePrefillMessage: () => string | null }) => unknown) =>
    sel({ consumePrefillMessage: () => null }),
}));

describe("assistant-api types", () => {
  it("exports sendAssistantMessage", async () => {
    const mod = await import("@/lib/assistant-api");
    expect(typeof mod.sendAssistantMessage).toBe("function");
    expect(typeof mod.submitAgentFeedback).toBe("function");
  });
});

describe("AGENT_META structure", () => {
  it("assistant chat component module loads", async () => {
    const mod = await import("@/components/assistant/assistant-chat");
    expect(mod.AssistantChat).toBeDefined();
  });
});

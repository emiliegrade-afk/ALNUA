import { describe, expect, it, vi } from "vitest";

import type { LiveTask, LiveVoiceSession } from "@/lib/live-api";
import {
  connectRealtime,
  errorFromEvent,
  extractFunctionCalls,
  IDLE_LIMIT_MS,
  isActivityEvent,
  isIdleExpired,
  isTrustedCallsUrl,
  nextVoiceState,
  parseRealtimeEvent,
  transcriptFromEvent,
  type RealtimeDeps,
} from "@/lib/live-realtime";
import { runVoiceTool, type VoiceToolApi } from "@/lib/live-voice-tools";
import { orbState } from "@/components/live/nadia-orb";

function task(over: Partial<LiveTask> = {}): LiveTask {
  return {
    id: "t1",
    agent_id: "secretary",
    instruction: "Programme du jour",
    status: "running",
    session_id: "live-voice",
    created_at: "",
    updated_at: "",
    started_at: null,
    finished_at: null,
    result: "",
    artifacts: [],
    file_ids: [],
    error: "",
    ...over,
  };
}

function toolApi(over: Partial<VoiceToolApi> = {}): VoiceToolApi {
  return {
    create: vi.fn(async () => task()),
    get: vi.fn(async () => task()),
    list: vi.fn(async () => [task()]),
    cancel: vi.fn(async () => task({ status: "cancelled" })),
    ...over,
  };
}

describe("realtime events", () => {
  it("ignores malformed payloads", () => {
    expect(parseRealtimeEvent("{nope")).toBeNull();
    expect(parseRealtimeEvent(42)).toBeNull();
    expect(parseRealtimeEvent('{"type":"x"}')).toEqual({ type: "x" });
  });

  it("extracts function calls from response.done only", () => {
    const done = {
      type: "response.done",
      response: {
        output: [
          { type: "message" },
          { type: "function_call", call_id: "c1", name: "start_task", arguments: '{"a":1}' },
          { type: "function_call", name: "no_call_id" },
        ],
      },
    };
    expect(extractFunctionCalls(done)).toEqual([
      { callId: "c1", name: "start_task", arguments: '{"a":1}' },
    ]);
    expect(extractFunctionCalls({ ...done, type: "response.created" })).toEqual([]);
  });

  it("reads transcripts and hides benign errors", () => {
    expect(
      transcriptFromEvent({
        type: "conversation.item.input_audio_transcription.completed",
        transcript: " bonjour ",
      }),
    ).toEqual({ role: "user", text: "bonjour" });
    expect(
      transcriptFromEvent({ type: "response.output_audio_transcript.done", transcript: "Salut" }),
    ).toEqual({ role: "assistant", text: "Salut" });
    expect(transcriptFromEvent({ type: "response.output_audio_transcript.done", transcript: " " })).toBeNull();

    expect(errorFromEvent({ type: "error", error: { message: "quota" } })).toBe("quota");
    expect(
      errorFromEvent({ type: "error", error: { code: "response_cancel_not_active", message: "x" } }),
    ).toBeNull();
  });

  it("follows the turns detected by the server", () => {
    expect(nextVoiceState("ready", { type: "input_audio_buffer.speech_started" })).toBe("listening");
    expect(nextVoiceState("listening", { type: "input_audio_buffer.speech_stopped" })).toBe("thinking");
    expect(nextVoiceState("thinking", { type: "output_audio_buffer.started" })).toBe("speaking");
    expect(nextVoiceState("speaking", { type: "output_audio_buffer.stopped" })).toBe("ready");
    // Barge-in: the user talks over Nadia.
    expect(nextVoiceState("speaking", { type: "input_audio_buffer.speech_started" })).toBe("listening");
    // The response object can complete while audio still plays.
    expect(nextVoiceState("speaking", { type: "response.done", response: { output: [] } })).toBe("speaking");
    expect(nextVoiceState("thinking", { type: "response.done", response: { output: [] } })).toBe("ready");
    expect(
      nextVoiceState("speaking", {
        type: "response.done",
        response: { output: [{ type: "function_call", call_id: "c", name: "list_tasks" }] },
      }),
    ).toBe("thinking");
    expect(nextVoiceState("idle", { type: "response.created" })).toBe("idle");
  });

  it("expires only a quiet session after the idle limit", () => {
    expect(isIdleExpired(0, IDLE_LIMIT_MS, "ready")).toBe(true);
    expect(isIdleExpired(0, IDLE_LIMIT_MS - 1, "ready")).toBe(false);
    for (const busy of ["listening", "thinking", "speaking"] as const) {
      expect(isIdleExpired(0, IDLE_LIMIT_MS * 10, busy)).toBe(false);
    }
    expect(isActivityEvent({ type: "input_audio_buffer.speech_started" })).toBe(true);
    expect(isActivityEvent({ type: "rate_limits.updated" })).toBe(false);
  });

  it("lets a live voice session win over the task feed in the orb", () => {
    expect(orbState("reconnecting", 0, "listening")).toBe("listening");
    expect(orbState("online", 2, "idle")).toBe("working");
    expect(orbState("reconnecting", 0, "ready")).toBe("offline");
  });
});

describe("voice tools", () => {
  it("merges composer file ids into start_task", async () => {
    const api = toolApi();
    const out = JSON.parse(
      await runVoiceTool(
        { name: "start_task", arguments: '{"agent":"coo","instruction":"Analyse"}' },
        () => undefined,
        api,
        { pendingFileIds: () => ["f1", "f2"] },
      ),
    );
    expect(api.create).toHaveBeenCalledWith({
      agent_id: "coo",
      instruction: "Analyse",
      session_id: "live-voice",
      file_ids: ["f1", "f2"],
    });
    expect(out.task_id).toBe("t1");
  });

  it("starts a task and mirrors it on screen", async () => {
    const api = toolApi();
    const onTask = vi.fn();
    const out = JSON.parse(
      await runVoiceTool(
        { name: "start_task", arguments: '{"agent":"plan","instruction":"Veille IA"}' },
        onTask,
        api,
      ),
    );
    expect(api.create).toHaveBeenCalledWith({
      agent_id: "plan",
      instruction: "Veille IA",
      session_id: "live-voice",
    });
    expect(onTask).toHaveBeenCalledOnce();
    expect(out).toMatchObject({ task_id: "t1", status: "running" });
  });

  it("rejects agents and instructions the model should not use", async () => {
    const api = toolApi();
    const bad = JSON.parse(
      await runVoiceTool({ name: "start_task", arguments: '{"agent":"dev_app","instruction":"x"}' }, undefined, api),
    );
    const empty = JSON.parse(
      await runVoiceTool({ name: "start_task", arguments: '{"agent":"coo","instruction":"  "}' }, undefined, api),
    );
    expect(bad.error).toBeTruthy();
    expect(empty.error).toBeTruthy();
    expect(api.create).not.toHaveBeenCalled();
  });

  it("truncates a long result and never throws", async () => {
    const long = "a".repeat(5000);
    const api = toolApi({ get: vi.fn(async () => task({ status: "done", result: long })) });
    const out = JSON.parse(
      await runVoiceTool({ name: "get_task_status", arguments: '{"task_id":"t1"}' }, undefined, api),
    );
    expect(out.result_preview.length).toBeLessThan(700);

    const failing = toolApi({ cancel: vi.fn(async () => Promise.reject(new Error("Tâche introuvable"))) });
    const err = JSON.parse(
      await runVoiceTool({ name: "cancel_task", arguments: '{"task_id":"zz"}' }, undefined, failing),
    );
    expect(err.error).toBe("Tâche introuvable");

    const cleared: string[] = [];
    const wipe = JSON.parse(
      await runVoiceTool(
        { name: "clear_screens", arguments: "{}" },
        undefined,
        api,
        { clearScreens: () => cleared.push("ok") },
      ),
    );
    expect(wipe.cleared).toBe(true);
    expect(cleared).toEqual(["ok"]);

    const unknown = JSON.parse(await runVoiceTool({ name: "rm_rf", arguments: "{}" }, undefined, api));
    expect(unknown.error).toContain("inconnu");
    const garbage = JSON.parse(await runVoiceTool({ name: "get_task_status", arguments: "not json" }, undefined, api));
    expect(garbage.error).toBeTruthy();
  });
});

describe("connectRealtime", () => {
  const session: LiveVoiceSession = {
    client_secret: "ek_test",
    calls_url: "https://api.openai.com/v1/realtime/calls",
    expires_at: null,
    model: "gpt-realtime",
    persona: "nadia",
    voice: "marin",
    session_id: "sess-1",
    remaining_seconds: 1800,
  };

  function rig(fetchStatus = 200) {
    const sent: object[] = [];
    const channel = {
      readyState: "open",
      send: vi.fn((raw: string) => sent.push(JSON.parse(raw))),
      close: vi.fn(),
      onmessage: null as ((m: { data: string }) => void) | null,
      onclose: null as (() => void) | null,
    };
    const peer = {
      createDataChannel: vi.fn(() => channel),
      addTrack: vi.fn(),
      createOffer: vi.fn(async () => ({ type: "offer", sdp: "v=0 offer" })),
      setLocalDescription: vi.fn(async () => undefined),
      setRemoteDescription: vi.fn(async () => undefined),
      close: vi.fn(),
      ontrack: null,
    };
    const track = { enabled: true, stop: vi.fn() };
    const mic = { getAudioTracks: () => [track], getTracks: () => [track] };
    const fetchImpl = vi.fn(async () => new Response("v=0 answer", { status: fetchStatus }));
    const deps = {
      createPeer: () => peer,
      getMicrophone: async () => mic,
      fetchImpl,
      createAudio: () => ({ srcObject: null }),
    } as unknown as RealtimeDeps;
    return { sent, channel, peer, track, fetchImpl, deps };
  }

  it("sends the SDP to OpenAI with the ephemeral secret, mic open", async () => {
    const r = rig();
    await connectRealtime(session, { onEvent: vi.fn(), onClosed: vi.fn() }, r.deps);
    const [url, init] = r.fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(session.calls_url);
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer ek_test");
    expect(init.body).toBe("v=0 offer");
    expect(r.track.enabled).toBe(true); // server VAD: no button to hold
    expect(r.peer.setRemoteDescription).toHaveBeenCalledWith({ type: "answer", sdp: "v=0 answer" });
  });

  it("never sends the secret anywhere but api.openai.com", async () => {
    const r = rig();
    expect(isTrustedCallsUrl("https://evil.example/v1/realtime/calls")).toBe(false);
    expect(isTrustedCallsUrl("http://api.openai.com/v1/realtime/calls")).toBe(false);
    await expect(
      connectRealtime({ ...session, calls_url: "https://evil.example/x" }, { onEvent: vi.fn(), onClosed: vi.fn() }, r.deps),
    ).rejects.toThrow();
    expect(r.fetchImpl).not.toHaveBeenCalled();
  });

  it("mute stops the audio at the source and unmute restores it", async () => {
    const r = rig();
    const conn = await connectRealtime(session, { onEvent: vi.fn(), onClosed: vi.fn() }, r.deps);
    conn.setMuted(true);
    expect(r.track.enabled).toBe(false);
    conn.setMuted(false);
    expect(r.track.enabled).toBe(true);
  });

  it("forwards server events and sends events on the open channel", async () => {
    const r = rig();
    const onEvent = vi.fn();
    const conn = await connectRealtime(session, { onEvent, onClosed: vi.fn() }, r.deps);
    r.channel.onmessage?.({ data: '{"type":"input_audio_buffer.speech_started"}' });
    r.channel.onmessage?.({ data: "garbage" });
    expect(onEvent).toHaveBeenCalledTimes(1);
    conn.send({ type: "response.create" });
    expect(r.sent).toEqual([{ type: "response.create" }]);
  });

  it("releases the microphone when OpenAI refuses the call", async () => {
    const r = rig(401);
    const onClosed = vi.fn();
    await expect(connectRealtime(session, { onEvent: vi.fn(), onClosed }, r.deps)).rejects.toThrow(/401/);
    expect(r.track.stop).toHaveBeenCalled();
    expect(r.peer.close).toHaveBeenCalled();
    expect(onClosed).toHaveBeenCalledOnce();
  });
});

/**
 * OpenAI Realtime over WebRTC (SPEC_JARVIS_LIVE Lot 3).
 *
 * The browser holds only the ephemeral secret minted by the Hub. The mic is open for
 * the whole session and OpenAI's server VAD decides when a turn starts and ends, so
 * the user just talks (and can cut Nadia off). Cost and privacy guards: a mute switch
 * and an idle timeout (see use-live-voice.ts).
 */

import type { LiveVoiceSession } from "./live-api";

export type VoiceState =
  | "idle"
  | "connecting"
  | "ready"
  | "listening"
  | "thinking"
  | "speaking"
  | "error";

export interface FunctionCall {
  callId: string;
  name: string;
  arguments: string;
}

export interface TranscriptLine {
  role: "user" | "assistant";
  text: string;
}

export type RealtimeEvent = { type?: unknown } & Record<string, unknown>;

export function parseRealtimeEvent(raw: unknown): RealtimeEvent | null {
  if (typeof raw !== "string") return null;
  try {
    const value: unknown = JSON.parse(raw);
    return typeof value === "object" && value !== null ? (value as RealtimeEvent) : null;
  } catch {
    return null;
  }
}

/** Function calls requested in a `response.done` event, in order. */
export function extractFunctionCalls(event: RealtimeEvent): FunctionCall[] {
  if (event.type !== "response.done") return [];
  const response = event.response as { output?: unknown } | undefined;
  if (!response || !Array.isArray(response.output)) return [];
  const calls: FunctionCall[] = [];
  for (const item of response.output as Record<string, unknown>[]) {
    if (
      item?.type === "function_call" &&
      typeof item.call_id === "string" &&
      typeof item.name === "string"
    ) {
      calls.push({
        callId: item.call_id,
        name: item.name,
        arguments: typeof item.arguments === "string" ? item.arguments : "{}",
      });
    }
  }
  return calls;
}

export function transcriptFromEvent(event: RealtimeEvent): TranscriptLine | null {
  const text = typeof event.transcript === "string" ? event.transcript.trim() : "";
  if (!text) return null;
  if (event.type === "conversation.item.input_audio_transcription.completed") {
    return { role: "user", text };
  }
  if (event.type === "response.output_audio_transcript.done") {
    return { role: "assistant", text };
  }
  return null;
}

const BENIGN_ERRORS: ReadonlySet<string> = new Set([
  "response_cancel_not_active",
  "input_audio_buffer_commit_empty",
]);

export function errorFromEvent(event: RealtimeEvent): string | null {
  if (event.type !== "error") return null;
  const err = event.error as { message?: unknown; code?: unknown } | undefined;
  if (typeof err?.code === "string" && BENIGN_ERRORS.has(err.code)) return null;
  return typeof err?.message === "string" ? err.message : "Erreur de la session vocale.";
}

/** Voice state implied by a server event (server VAD drives the turns). */
export function nextVoiceState(current: VoiceState, event: RealtimeEvent): VoiceState {
  if (current === "idle" || current === "connecting" || current === "error") return current;
  switch (event.type) {
    case "input_audio_buffer.speech_started":
      return "listening";
    case "input_audio_buffer.speech_stopped":
    case "response.created":
      return "thinking";
    case "output_audio_buffer.started":
    case "response.output_audio_transcript.delta":
      return "speaking";
    case "output_audio_buffer.stopped":
      return current === "speaking" ? "ready" : current;
    case "response.done":
      if (extractFunctionCalls(event).length > 0) return "thinking";
      // The audio can still be playing when the response object is complete.
      return current === "speaking" ? current : "ready";
    default:
      return current;
  }
}

/** Without exchange for this long, an open mic only costs money: the session is closed. */
export const IDLE_LIMIT_MS = 90_000;

const ACTIVITY_EVENTS: ReadonlySet<string> = new Set([
  "input_audio_buffer.speech_started",
  "response.created",
  "output_audio_buffer.started",
  "response.done",
]);

export function isActivityEvent(event: RealtimeEvent): boolean {
  return typeof event.type === "string" && ACTIVITY_EVENTS.has(event.type);
}

/** Only a quiet session ("ready") can expire: never cut someone off mid-exchange. */
export function isIdleExpired(
  lastActivityMs: number,
  nowMs: number,
  state: VoiceState,
  limitMs: number = IDLE_LIMIT_MS,
): boolean {
  return state === "ready" && nowMs - lastActivityMs >= limitMs;
}

export function toolOutputEvents(callId: string, output: string): object[] {
  return [
    {
      type: "conversation.item.create",
      item: { type: "function_call_output", call_id: callId, output },
    },
  ];
}

export interface RealtimeDeps {
  createPeer: () => RTCPeerConnection;
  getMicrophone: () => Promise<MediaStream>;
  fetchImpl: typeof fetch;
  createAudio: () => HTMLAudioElement;
}

const defaultDeps: RealtimeDeps = {
  createPeer: () => new RTCPeerConnection(),
  // Echo cancellation matters: with speakers, the mic would otherwise hear Nadia
  // and interrupt her. Headphones remain the reliable fix.
  getMicrophone: () =>
    navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    }),
  fetchImpl: (...args) => fetch(...args),
  createAudio: () => {
    const audio = new Audio();
    audio.autoplay = true;
    return audio;
  },
};

export interface RealtimeHandlers {
  onEvent: (event: RealtimeEvent) => void;
  onClosed: () => void;
}

export interface RealtimeConnection {
  send: (event: object) => void;
  /** Mute stops audio at the source: nothing is sent to OpenAI while muted. */
  setMuted: (muted: boolean) => void;
  close: () => void;
}

/** Only OpenAI's own endpoint may receive the ephemeral secret. */
export function isTrustedCallsUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" && parsed.hostname === "api.openai.com";
  } catch {
    return false;
  }
}

export async function connectRealtime(
  session: LiveVoiceSession,
  handlers: RealtimeHandlers,
  deps: RealtimeDeps = defaultDeps,
): Promise<RealtimeConnection> {
  if (!isTrustedCallsUrl(session.calls_url)) {
    throw new Error("Adresse de session vocale refusée.");
  }
  const peer = deps.createPeer();
  const audio = deps.createAudio();
  // Channel before the offer, so it is part of the SDP.
  const channel = peer.createDataChannel("oai-events");
  let microphone: MediaStream | null = null;
  let closed = false;

  const close = () => {
    if (closed) return;
    closed = true;
    microphone?.getTracks().forEach((track) => track.stop());
    audio.srcObject = null;
    channel.close();
    peer.close();
    handlers.onClosed();
  };

  peer.ontrack = (event) => {
    audio.srcObject = event.streams[0] ?? null;
  };
  channel.onmessage = (message) => {
    const event = parseRealtimeEvent(message.data);
    if (event) handlers.onEvent(event);
  };
  channel.onclose = close;

  try {
    microphone = await deps.getMicrophone();
    for (const track of microphone.getAudioTracks()) {
      peer.addTrack(track, microphone);
    }

    const offer = await peer.createOffer();
    await peer.setLocalDescription(offer);
    const response = await deps.fetchImpl(session.calls_url, {
      method: "POST",
      body: offer.sdp,
      headers: {
        Authorization: `Bearer ${session.client_secret}`,
        "Content-Type": "application/sdp",
      },
    });
    if (!response.ok) throw new Error(`Connexion vocale refusée (${response.status}).`);
    await peer.setRemoteDescription({ type: "answer", sdp: await response.text() });
  } catch (err) {
    close();
    throw err;
  }

  const send = (event: object) => {
    if (channel.readyState === "open") channel.send(JSON.stringify(event));
  };
  return {
    send,
    close,
    setMuted: (muted) =>
      microphone?.getAudioTracks().forEach((track) => {
        track.enabled = !muted;
      }),
  };
}

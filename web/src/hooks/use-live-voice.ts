"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  createLiveSession,
  endLiveSession,
  getLiveUsage,
  type LivePersona,
  type LiveTask,
  type LiveUsage,
} from "@/lib/live-api";
import {
  connectRealtime,
  errorFromEvent,
  extractFunctionCalls,
  IDLE_LIMIT_MS,
  isActivityEvent,
  isIdleExpired,
  nextVoiceState,
  toolOutputEvents,
  transcriptFromEvent,
  type RealtimeConnection,
  type RealtimeEvent,
  type TranscriptLine,
  type VoiceState,
} from "@/lib/live-realtime";
import { wantsClearScreens } from "@/lib/live-clear";
import { completionEvents } from "@/lib/live-voice-reply";
import { runVoiceTool } from "@/lib/live-voice-tools";
import { useLiveStore } from "@/store/live-store";

const TRANSCRIPT_LINES = 6;
const IDLE_CHECK_MS = 5_000;
const IDLE_NOTICE = "Session vocale fermée après 90 s sans échange.";
const CAP_NOTICE = "Plafond quotidien de voix atteint : utilise le clavier.";

export interface LiveVoice {
  state: VoiceState;
  transcript: TranscriptLine[];
  error: string | null;
  connect: (persona: LivePersona) => Promise<void>;
  disconnect: () => void;
  muted: boolean;
  toggleMute: () => void;
  announce: (task: LiveTask) => void;
  remainingSeconds: number | null;
}

/** Voice session lifecycle for the cockpit. Tasks started by voice are mirrored via onTask. */
export function useLiveVoice(onTask: (task: LiveTask) => void): LiveVoice {
  const [state, setStateValue] = useState<VoiceState>("idle");
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [muted, setMuted] = useState(false);
  const [remainingSeconds, setRemaining] = useState<number | null>(null);
  const lastActivity = useRef(Date.now());
  const connection = useRef<RealtimeConnection | null>(null);
  const sessionId = useRef("");
  const startedAt = useRef(0);
  const capTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pending = useRef<LiveTask[]>([]);
  const stateRef = useRef<VoiceState>("idle");
  const onTaskRef = useRef(onTask);
  onTaskRef.current = onTask;

  const setState = useCallback((next: VoiceState) => {
    stateRef.current = next;
    setStateValue(next);
  }, []);

  const applyUsage = useCallback((usage: LiveUsage) => {
    setRemaining(usage.remaining_seconds);
  }, []);

  const reportSession = useCallback(() => {
    const id = sessionId.current;
    const start = startedAt.current;
    sessionId.current = "";
    startedAt.current = 0;
    if (capTimer.current) {
      clearTimeout(capTimer.current);
      capTimer.current = null;
    }
    if (!id || !start) return;
    void endLiveSession(id, (Date.now() - start) / 1000)
      .then(applyUsage)
      .catch(() => undefined);
  }, [applyUsage]);

  const speakAbout = useCallback((task: LiveTask) => {
    if (!connection.current) return;
    for (const event of completionEvents(task)) connection.current.send(event);
  }, []);

  const flushPending = useCallback(() => {
    if (stateRef.current === "listening") return;
    const next = pending.current.shift();
    if (next) speakAbout(next);
  }, [speakAbout]);

  const handleEvent = useCallback(
    (event: RealtimeEvent) => {
      if (isActivityEvent(event)) lastActivity.current = Date.now();
      const failure = errorFromEvent(event);
      if (failure) setError(failure);

      const line = transcriptFromEvent(event);
      if (line) {
        setTranscript((prev) => [...prev, line].slice(-TRANSCRIPT_LINES));
        if (line.role === "user" && wantsClearScreens(line.text)) {
          useLiveStore.getState().clearScreens();
        }
      }

      const calls = extractFunctionCalls(event);
      if (calls.length > 0) {
        void Promise.all(
          calls.map(async (call) => ({
            call,
            output: await runVoiceTool(
              call,
              (task) => onTaskRef.current(task),
              undefined,
              {
                pendingFileIds: () => useLiveStore.getState().composerFileIds,
                clearScreens: () => useLiveStore.getState().clearScreens(),
              },
            ),
          })),
        ).then((results) => {
          for (const { call, output } of results) {
            for (const reply of toolOutputEvents(call.callId, output)) {
              connection.current?.send(reply);
            }
          }
          connection.current?.send({ type: "response.create" });
        });
      }

      setState(nextVoiceState(stateRef.current, event));
      flushPending();
    },
    [flushPending, setState],
  );

  const disconnect = useCallback(() => {
    connection.current?.close();
    connection.current = null;
    pending.current = [];
    reportSession();
    setMuted(false);
    setState("idle");
  }, [reportSession, setState]);

  const connect = useCallback(
    async (persona: LivePersona) => {
      if (connection.current) return;
      setError(null);
      setTranscript([]);
      setMuted(false);
      lastActivity.current = Date.now();
      setState("connecting");
      try {
        const session = await createLiveSession(persona);
        sessionId.current = session.session_id;
        startedAt.current = Date.now();
        if (session.remaining_seconds !== null) {
          setRemaining(session.remaining_seconds);
          capTimer.current = setTimeout(() => {
            disconnect();
            setError(CAP_NOTICE);
          }, session.remaining_seconds * 1000);
        }
        connection.current = await connectRealtime(session, {
          onEvent: handleEvent,
          onClosed: () => {
            connection.current = null;
            reportSession();
            setState("idle");
          },
        });
        setState("ready");
      } catch (err) {
        connection.current = null;
        reportSession();
        setError(err instanceof Error ? err.message : "Connexion vocale impossible.");
        setState("error");
      }
    },
    [disconnect, handleEvent, reportSession, setState],
  );

  const toggleMute = useCallback(() => {
    if (!connection.current) return;
    const next = !muted;
    connection.current.setMuted(next);
    lastActivity.current = Date.now();
    setMuted(next);
  }, [muted]);

  const announce = useCallback(
    (task: LiveTask) => {
      if (!connection.current) return;
      if (stateRef.current === "listening") {
        pending.current.push(task);
        return;
      }
      speakAbout(task);
    },
    [speakAbout],
  );

  useEffect(() => {
    void getLiveUsage().then(applyUsage).catch(() => undefined);
  }, [applyUsage]);

  useEffect(() => {
    if (state === "idle" || state === "error") return;
    const timer = setInterval(() => {
      if (isIdleExpired(lastActivity.current, Date.now(), stateRef.current, IDLE_LIMIT_MS)) {
        disconnect();
        setError(IDLE_NOTICE);
      }
    }, IDLE_CHECK_MS);
    return () => clearInterval(timer);
  }, [state, disconnect]);

  useEffect(() => () => connection.current?.close(), []);

  return {
    state,
    transcript,
    error,
    connect,
    disconnect,
    muted,
    toggleMute,
    announce,
    remainingSeconds,
  };
}

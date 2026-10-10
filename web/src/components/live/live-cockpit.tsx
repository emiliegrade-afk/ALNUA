"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Eraser } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useLiveStream } from "@/hooks/use-live-stream";
import { useLiveVoice } from "@/hooks/use-live-voice";
import { cancelLiveTask, createLiveTask, type LiveAgentId } from "@/lib/live-api";
import { buildResultCard, type ResultCard } from "@/lib/live-cards";
import { newlyFinished } from "@/lib/live-voice-reply";
import {
  isActive,
  newestFirst,
  useLiveStore,
  visibleScreens,
} from "@/store/live-store";

import { LiveAccessPanel } from "./live-access-panel";
import { LiveActivityRail } from "./live-activity-rail";
import { LiveCallStage } from "./live-call-stage";
import { LiveComposer } from "./live-composer";
import { LiveResultScreens } from "./live-result-screens";
import { LiveTaskPanel } from "./live-task-panel";
import { LiveVoiceControls } from "./live-voice-controls";
import { NadiaModeRail } from "./nadia-mode-rail";

const PANEL_LIMIT = 12;

/** Nadia cockpit: task panel + result screens + keyboard input (SPEC_JARVIS_LIVE §14). */
export function LiveCockpit() {
  useLiveStream();

  const tasks = useLiveStore((s) => s.tasks);
  const cleared = useLiveStore((s) => s.cleared);
  const upsert = useLiveStore((s) => s.upsert);
  const clearScreens = useLiveStore((s) => s.clearScreens);
  const dismiss = useLiveStore((s) => s.dismiss);
  const [error, setError] = useState<string | null>(null);
  const voice = useLiveVoice(upsert);
  const announce = voice.announce;
  const watched = useRef(new Set<string>());

  useEffect(() => {
    const { next, finished } = newlyFinished(watched.current, Object.values(tasks));
    watched.current = next;
    for (const task of finished) announce(task);
  }, [tasks, announce]);

  const panelTasks = useMemo(() => newestFirst(tasks).slice(0, PANEL_LIMIT), [tasks]);
  const activeCount = useMemo(
    () => Object.values(tasks).filter(isActive).length,
    [tasks],
  );
  const cards = useMemo(
    () =>
      visibleScreens(tasks, cleared)
        .map(buildResultCard)
        .filter((c): c is ResultCard => c !== null),
    [tasks, cleared],
  );

  const submit = useCallback(
    async (agent: LiveAgentId, instruction: string, fileIds: string[]) => {
      setError(null);
      try {
        upsert(
          await createLiveTask({
            agent_id: agent,
            instruction,
            file_ids: fileIds.length ? fileIds : undefined,
          }),
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Envoi impossible.");
      }
    },
    [upsert],
  );

  const cancel = useCallback(
    async (taskId: string) => {
      try {
        upsert(await cancelLiveTask(taskId));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Annulation impossible.");
      }
    },
    [upsert],
  );

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 text-ivory">
      <NadiaModeRail />
      <header className="flex justify-end">
        <Button variant="outline" size="sm" onClick={clearScreens} disabled={cards.length === 0}>
          <Eraser />
          Tout effacer
        </Button>
      </header>

      <LiveCallStage voice={voice} activeCount={activeCount} />
      <LiveVoiceControls voice={voice} />
      <LiveAccessPanel />
      <LiveActivityRail tasks={panelTasks} />

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[18rem_1fr]">
        <LiveTaskPanel tasks={panelTasks} onCancel={cancel} />
        <LiveResultScreens cards={cards} onDismiss={dismiss} />
      </div>

      <LiveComposer error={error} onSubmit={submit} />
    </div>
  );
}

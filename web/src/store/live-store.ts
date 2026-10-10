import { create } from "zustand";

import type { LiveTask } from "@/lib/live-api";

export type LiveConnection = "connecting" | "online" | "reconnecting";

const FINISHED = new Set(["done", "failed"]);
const ACTIVE = new Set(["queued", "running"]);

export function isActive(task: LiveTask): boolean {
  return ACTIVE.has(task.status);
}

export function newestFirst(tasks: Record<string, LiveTask>): LiveTask[] {
  return Object.values(tasks).sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  );
}

/** Tasks whose result belongs on a screen: finished and not cleared by the user. */
export function visibleScreens(
  tasks: Record<string, LiveTask>,
  cleared: ReadonlySet<string>,
): LiveTask[] {
  return newestFirst(tasks).filter(
    (t) => FINISHED.has(t.status) && !cleared.has(t.id),
  );
}

interface LiveStore {
  tasks: Record<string, LiveTask>;
  cleared: Set<string>;
  connection: LiveConnection;
  /** File ids selected in Live composer — also applied to voice start_task. */
  composerFileIds: string[];
  upsert: (task: LiveTask) => void;
  setConnection: (connection: LiveConnection) => void;
  setComposerFileIds: (ids: string[]) => void;
  /** "Tout effacer": empties the screens, never touches the tasks themselves. */
  clearScreens: () => void;
  dismiss: (taskId: string) => void;
}

export const useLiveStore = create<LiveStore>((set, get) => ({
  tasks: {},
  cleared: new Set<string>(),
  connection: "connecting",
  composerFileIds: [],
  setComposerFileIds: (ids) => set({ composerFileIds: ids }),
  upsert: (task) =>
    set((state) => {
      const current = state.tasks[task.id];
      // Ignore stale frames (e.g. a replayed snapshot older than what we hold).
      if (current && current.updated_at > task.updated_at) return state;
      return { tasks: { ...state.tasks, [task.id]: task } };
    }),
  setConnection: (connection) => set({ connection }),
  clearScreens: () => {
    const { tasks, cleared } = get();
    const next = new Set(cleared);
    for (const t of Object.values(tasks)) {
      if (FINISHED.has(t.status)) next.add(t.id);
    }
    set({ cleared: next });
  },
  dismiss: (taskId) =>
    set((state) => ({ cleared: new Set(state.cleared).add(taskId) })),
}));

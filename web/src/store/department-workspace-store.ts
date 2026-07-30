import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type WorkspaceTab =
  | "equipe"
  | "projets"
  | "missions"
  | "backlog"
  | "documentation";

interface DepartmentWorkspaceStore {
  activeTabByDept: Partial<Record<string, WorkspaceTab>>;
  setActiveTab: (deptId: string, tab: WorkspaceTab) => void;
  getActiveTab: (deptId: string) => WorkspaceTab;
}

/**
 * Each department (/app, /gaming, ...) is a distinct Next.js route — the
 * component tree unmounts on navigation, so a plain useState loses the
 * active tab every time. sessionStorage (not localStorage): no need to
 * survive past the browser session, keeps a clean "back to Équipe" default
 * after a real restart instead of indefinitely stale state.
 */
export const useDepartmentWorkspaceStore = create<DepartmentWorkspaceStore>()(
  persist(
    (set, get) => ({
      activeTabByDept: {},
      setActiveTab: (deptId, tab) =>
        set((s) => ({ activeTabByDept: { ...s.activeTabByDept, [deptId]: tab } })),
      getActiveTab: (deptId) => get().activeTabByDept[deptId] ?? "equipe",
    }),
    {
      name: "department-workspace-store",
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);

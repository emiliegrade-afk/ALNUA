import { describe, it, expect, beforeEach } from "vitest";
import { useDepartmentWorkspaceStore } from "./department-workspace-store";

describe("useDepartmentWorkspaceStore", () => {
  beforeEach(() => {
    sessionStorage.clear();
    useDepartmentWorkspaceStore.setState({ activeTabByDept: {} });
  });

  it("defaults to 'equipe' for a department never visited", () => {
    expect(useDepartmentWorkspaceStore.getState().getActiveTab("app")).toBe("equipe");
  });

  it("remembers the active tab per department independently", () => {
    const { setActiveTab, getActiveTab } = useDepartmentWorkspaceStore.getState();
    setActiveTab("app", "missions");
    setActiveTab("gaming", "projets");

    expect(getActiveTab("app")).toBe("missions");
    expect(getActiveTab("gaming")).toBe("projets");
    // A third department never touched still falls back to the default —
    // this is the exact regression the Design Review flagged: switching
    // departments must not reset an already-visited one back to "equipe".
    expect(getActiveTab("robo")).toBe("equipe");
  });

  it("persists to sessionStorage so a refresh doesn't lose the active tab", () => {
    useDepartmentWorkspaceStore.getState().setActiveTab("app", "missions");
    const raw = sessionStorage.getItem("department-workspace-store");
    expect(raw).toBeTruthy();
    expect(JSON.parse(raw!).state.activeTabByDept.app).toBe("missions");
  });
});

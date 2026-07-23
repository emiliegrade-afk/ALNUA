"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  IdeActivityBar,
  IdeAiToggleStrip,
  type SidebarView,
} from "./ide-activity-bar";
import { IdeAiPanel, type CoachMessage } from "./ide-ai-panel";
import {
  IdeBottomPanel,
  type BottomPanelTab,
} from "./ide-bottom-panel";
import { IdeEditorArea, type EditorTab } from "./ide-editor-area";
import { IdeQuickOpen } from "./ide-quick-open";
import { IdeSidebar } from "./ide-sidebar";
import { IdeStatusBar } from "./ide-status-bar";
import { ResizeHandle } from "./use-panel-resize";
import {
  askCodingCoach,
  codingAgentLabel,
  fetchIdeDiff,
  fetchIdeFile,
  fetchIdeHermesCatalog,
  fetchIdeLive,
  fetchIdeTree,
  fetchIdeWorkspaces,
  runSandboxCommand,
  saveIdeFile,
  type IdeTreeEntry,
  type IdeLiveTask,
  type IdeWorkspace,
} from "@/lib/ide-api";

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n));
}

function collectFilePaths(entries: IdeTreeEntry[]): string[] {
  return entries.filter((e) => e.type === "file").map((e) => e.path);
}

const INITIAL_COACH: CoachMessage[] = [
  {
    role: "assistant",
    content:
      "Salut — c'est **Luca**, ton coach code ALNUA.\n\nOuvre un fichier, pose une question, ou demande-moi d'expliquer / corriger ce que tu vois. J'ai le contexte du fichier actif.",
  },
];

export function HubIde() {
  const [workspaces, setWorkspaces] = useState<IdeWorkspace[]>([]);
  const [workspace, setWorkspace] = useState("sandbox");
  const [readOnly, setReadOnly] = useState(false);
  const [rootEntries, setRootEntries] = useState<IdeTreeEntry[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ ".": true });
  const [fileFilter, setFileFilter] = useState("");
  const [knownFiles, setKnownFiles] = useState<string[]>([]);

  const [tabs, setTabs] = useState<EditorTab[]>([]);
  const [activePath, setActivePath] = useState<string | null>(null);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarView, setSidebarView] = useState<SidebarView>("explorer");
  const [sidebarWidth, setSidebarWidth] = useState(260);

  const [aiOpen, setAiOpen] = useState(true);
  const [aiWidth, setAiWidth] = useState(380);

  const [bottomOpen, setBottomOpen] = useState(true);
  const [bottomHeight, setBottomHeight] = useState(200);
  const [bottomTab, setBottomTab] = useState<BottomPanelTab>("terminal");

  const [quickOpen, setQuickOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [apiOnline, setApiOnline] = useState(true);

  const [liveTasks, setLiveTasks] = useState<IdeLiveTask[]>([]);
  const [diff, setDiff] = useState("");
  const [terminalCmd, setTerminalCmd] = useState("python hello.py");
  const [terminalHistory, setTerminalHistory] = useState<
    Array<{ cmd: string; output: string; exitCode: number }>
  >([]);

  const [coachMessages, setCoachMessages] = useState<CoachMessage[]>(INITIAL_COACH);
  const [coachInput, setCoachInput] = useState("");
  const [coachLoading, setCoachLoading] = useState(false);
  const [hermesOk, setHermesOk] = useState(false);

  const [cursorLine, setCursorLine] = useState(1);
  const [cursorCol, setCursorCol] = useState(1);

  const activeTab = tabs.find((t) => t.path === activePath) ?? null;
  const workspaceLabel =
    workspaces.find((w) => w.id === workspace)?.label ?? workspace;

  const quickOpenFiles = useMemo(() => {
    const all = new Set([...knownFiles, ...tabs.map((t) => t.path)]);
    return Array.from(all).sort();
  }, [knownFiles, tabs]);

  const reloadWorkspaces = useCallback(async () => {
    try {
      const list = await fetchIdeWorkspaces();
      setWorkspaces(list);
      setApiOnline(true);
      const agent = list.find((w) => w.active);
      if (agent && workspace === "sandbox" && agent.id === "agent") {
        setWorkspace("agent");
      }
    } catch (e) {
      setApiOnline(false);
      setError(e instanceof Error ? e.message : "IDE indisponible");
    }
  }, [workspace]);

  const reloadTree = useCallback(async () => {
    try {
      const r = await fetchIdeTree(workspace, ".");
      setRootEntries(r.entries);
      setReadOnly(r.readOnly);
      setKnownFiles((prev) => {
        const next = new Set(prev);
        collectFilePaths(r.entries).forEach((p) => next.add(p));
        return Array.from(next);
      });
      setError(null);
      setApiOnline(true);
    } catch (e) {
      setApiOnline(false);
      setError(e instanceof Error ? e.message : "Arbre indisponible");
    }
  }, [workspace]);

  const reloadDiff = useCallback(async () => {
    try {
      const d = await fetchIdeDiff(workspace);
      setDiff(d);
    } catch {
      setDiff("");
    }
  }, [workspace]);

  const openFile = useCallback(
    async (path: string) => {
      const existing = tabs.find((t) => t.path === path);
      if (existing) {
        setActivePath(path);
        return;
      }
      try {
        const f = await fetchIdeFile(workspace, path);
        const tab: EditorTab = {
          path: f.path,
          content: f.content,
          language: f.language,
          dirty: false,
          readOnly: f.readOnly,
        };
        setTabs((prev) => [...prev, tab]);
        setActivePath(f.path);
        setReadOnly(f.readOnly);
        setKnownFiles((prev) => (prev.includes(path) ? prev : [...prev, path]));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Lecture impossible");
      }
    },
    [tabs, workspace],
  );

  const handleSave = useCallback(async () => {
    if (!activeTab || activeTab.readOnly || !activeTab.dirty) return;
    setSaving(true);
    try {
      await saveIdeFile(workspace, activeTab.path, activeTab.content);
      setTabs((prev) =>
        prev.map((t) =>
          t.path === activeTab.path ? { ...t, dirty: false } : t,
        ),
      );
      void reloadDiff();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sauvegarde échouée");
    } finally {
      setSaving(false);
    }
  }, [activeTab, reloadDiff, workspace]);

  const closeTab = useCallback(
    (path: string) => {
      setTabs((prev) => {
        const idx = prev.findIndex((t) => t.path === path);
        if (idx < 0) return prev;
        const next = prev.filter((t) => t.path !== path);
        if (activePath === path) {
          const fallback = next[idx] ?? next[idx - 1] ?? null;
          setActivePath(fallback?.path ?? null);
        }
        return next;
      });
    },
    [activePath],
  );

  const handleRun = useCallback(async () => {
    if (workspace !== "sandbox") {
      setTerminalHistory((h) => [
        ...h,
        {
          cmd: terminalCmd,
          output: "Terminal disponible uniquement dans le bac à sable.",
          exitCode: 1,
        },
      ]);
      return;
    }
    setRunning(true);
    try {
      const r = await runSandboxCommand(terminalCmd);
      setTerminalHistory((h) => [
        ...h,
        { cmd: terminalCmd, output: r.output, exitCode: r.exitCode },
      ]);
      setBottomTab("terminal");
      setBottomOpen(true);
    } catch (e) {
      setTerminalHistory((h) => [
        ...h,
        {
          cmd: terminalCmd,
          output: e instanceof Error ? e.message : "Erreur",
          exitCode: 1,
        },
      ]);
    } finally {
      setRunning(false);
    }
  }, [terminalCmd, workspace]);

  const sendCoach = useCallback(async () => {
    const msg = coachInput.trim();
    if (!msg || coachLoading) return;
    setCoachInput("");
    setCoachMessages((m) => [...m, { role: "user", content: msg }]);
    setCoachLoading(true);
    setAiOpen(true);
    try {
      const reply = await askCodingCoach(msg, {
        workspace,
        filePath: activeTab?.path,
        fileContent: activeTab?.content,
      });
      setCoachMessages((m) => [...m, { role: "assistant", content: reply }]);
    } catch (e) {
      setCoachMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: `Erreur : ${e instanceof Error ? e.message : "coach indisponible"}`,
        },
      ]);
    } finally {
      setCoachLoading(false);
    }
  }, [activeTab, coachInput, coachLoading, workspace]);

  const changeWorkspace = useCallback((id: string) => {
    setWorkspace(id);
    setTabs([]);
    setActivePath(null);
    setExpanded({ ".": true });
    setFileFilter("");
  }, []);

  useEffect(() => {
    void reloadWorkspaces();
    void fetchIdeHermesCatalog()
      .then((c) => setHermesOk(c.available))
      .catch(() => setHermesOk(false));
    const t = setInterval(() => {
      void reloadWorkspaces();
      void fetchIdeLive()
        .then((l) => setLiveTasks(l.active))
        .catch(() => setLiveTasks([]));
    }, 4000);
    return () => clearInterval(t);
  }, [reloadWorkspaces]);

  useEffect(() => {
    void reloadTree();
    void reloadDiff();
  }, [reloadDiff, reloadTree]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const mod = e.ctrlKey || e.metaKey;
      if (!mod) return;
      if (e.key === "s") {
        e.preventDefault();
        void handleSave();
      } else if (e.key === "p") {
        e.preventDefault();
        setQuickOpen(true);
      } else if (e.key === "b") {
        e.preventDefault();
        setSidebarOpen((v) => !v);
      } else if (e.key === "l") {
        e.preventDefault();
        setAiOpen((v) => !v);
      } else if (e.key === "`") {
        e.preventDefault();
        setBottomOpen((v) => !v);
      } else if (e.key === "w" && activePath) {
        e.preventDefault();
        closeTab(activePath);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [activePath, closeTab, handleSave]);

  const activeAgentLabel = liveTasks[0]
    ? `${codingAgentLabel(liveTasks[0].agent_id)} · #${liveTasks[0].issue_number} · ${liveTasks[0].progress ?? 0}%`
    : undefined;

  return (
    <div className="flex h-full min-h-0 flex-col bg-obsidian text-ivoire">
      {error ? (
        <p className="shrink-0 border-b border-red-500/30 bg-red-500/10 px-3 py-1 text-xs text-red-200">
          {error}
        </p>
      ) : null}

      <div className="flex min-h-0 flex-1">
        <IdeActivityBar
          sidebarView={sidebarView}
          sidebarOpen={sidebarOpen}
          aiOpen={aiOpen}
          bottomOpen={bottomOpen}
          onViewChange={setSidebarView}
          onToggleSidebar={() => setSidebarOpen((v) => !v)}
          onToggleAi={() => setAiOpen((v) => !v)}
          onToggleBottom={() => setBottomOpen((v) => !v)}
        />

        {sidebarOpen ? (
          <>
            <div
              className="shrink-0 overflow-hidden"
              style={{ width: sidebarWidth }}
            >
              <IdeSidebar
                view={sidebarView}
                workspace={workspace}
                workspaces={workspaces}
                rootEntries={rootEntries}
                selectedPath={activePath}
                fileFilter={fileFilter}
                expanded={expanded}
                readOnly={readOnly}
                activeAgent={activeAgentLabel}
                onWorkspaceChange={changeWorkspace}
                onFilterChange={setFileFilter}
                onSelectFile={(p) => void openFile(p)}
                onExpand={(p) =>
                  setExpanded((prev) => ({ ...prev, [p]: !prev[p] }))
                }
                onRefresh={() => {
                  void reloadTree();
                  void reloadWorkspaces();
                }}
              />
            </div>
            <ResizeHandle
              axis="horizontal"
              onDelta={(d) =>
                setSidebarWidth((w) => clamp(w + d, 180, 480))
              }
            />
          </>
        ) : null}

        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            <IdeEditorArea
              tabs={tabs}
              activePath={activePath}
              onSelectTab={setActivePath}
              onCloseTab={closeTab}
              onChangeContent={(path, content) => {
                setTabs((prev) =>
                  prev.map((t) =>
                    t.path === path ? { ...t, content, dirty: true } : t,
                  ),
                );
              }}
              cursorLine={cursorLine}
              cursorCol={cursorCol}
              onCursorChange={(line, col) => {
                setCursorLine(line);
                setCursorCol(col);
              }}
            />

            {aiOpen ? (
              <>
                <ResizeHandle
                  axis="horizontal"
                  onDelta={(d) =>
                    setAiWidth((w) => clamp(w - d, 280, 560))
                  }
                />
                <div
                  className="shrink-0 overflow-hidden"
                  style={{ width: aiWidth }}
                >
                  <IdeAiPanel
                    messages={coachMessages}
                    input={coachInput}
                    loading={coachLoading}
                    hermesOk={hermesOk}
                    onInputChange={setCoachInput}
                    onSend={() => void sendCoach()}
                    onClose={() => setAiOpen(false)}
                  />
                </div>
              </>
            ) : (
              <IdeAiToggleStrip onOpen={() => setAiOpen(true)} />
            )}
          </div>

          {bottomOpen ? (
            <>
              <ResizeHandle
                axis="vertical"
                onDelta={(d) =>
                  setBottomHeight((h) =>
                    clamp(h + d, 100, Math.floor(window.innerHeight * 0.5)),
                  )
                }
              />
              <div style={{ height: bottomHeight }}>
                <IdeBottomPanel
                  open={bottomOpen}
                  tab={bottomTab}
                  workspace={workspace}
                  terminalCmd={terminalCmd}
                  terminalHistory={terminalHistory}
                  liveTasks={liveTasks}
                  diff={diff}
                  onTabChange={setBottomTab}
                  onClose={() => setBottomOpen(false)}
                  onCmdChange={setTerminalCmd}
                  onRun={() => void handleRun()}
                  running={running}
                />
              </div>
            </>
          ) : null}
        </div>
      </div>

      <IdeStatusBar
        workspaceLabel={workspaceLabel}
        filePath={activePath}
        language={activeTab?.language ?? "plaintext"}
        line={cursorLine}
        col={cursorCol}
        dirty={activeTab?.dirty ?? false}
        readOnly={activeTab?.readOnly ?? readOnly}
        apiOnline={apiOnline}
        saving={saving}
        onSave={() => void handleSave()}
      />

      <IdeQuickOpen
        open={quickOpen}
        files={quickOpenFiles}
        onClose={() => setQuickOpen(false)}
        onSelect={(p) => void openFile(p)}
      />
    </div>
  );
}

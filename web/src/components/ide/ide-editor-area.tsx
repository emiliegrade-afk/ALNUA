"use client";

import dynamic from "next/dynamic";
import { X, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ALNUA_MONACO_THEME,
  MONACO_EDITOR_OPTIONS,
  registerAlnuaMonacoTheme,
} from "./monaco-alnua-theme";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-sm text-titane/50">
      Chargement éditeur…
    </div>
  ),
});

export interface EditorTab {
  path: string;
  content: string;
  language: string;
  dirty: boolean;
  readOnly: boolean;
}

function fileName(path: string) {
  const parts = path.split("/");
  return parts[parts.length - 1] || path;
}

export function IdeEditorArea({
  tabs,
  activePath,
  onSelectTab,
  onCloseTab,
  onChangeContent,
  cursorLine,
  cursorCol,
  onCursorChange,
}: {
  tabs: EditorTab[];
  activePath: string | null;
  onSelectTab: (path: string) => void;
  onCloseTab: (path: string) => void;
  onChangeContent: (path: string, content: string) => void;
  cursorLine: number;
  cursorCol: number;
  onCursorChange: (line: number, col: number) => void;
}) {
  const active = tabs.find((t) => t.path === activePath) ?? null;

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col bg-obsidian">
      {tabs.length > 0 ? (
        <div className="flex shrink-0 overflow-x-auto border-b border-bronze-faint bg-obsidian-2/80">
          {tabs.map((tab) => {
            const activeTab = tab.path === activePath;
            return (
              <div
                key={tab.path}
                className={cn(
                  "group flex max-w-[200px] shrink-0 items-center gap-1 border-r border-bronze-faint px-3 py-1.5 font-mono text-[11px] transition-colors",
                  activeTab
                    ? "bg-obsidian text-ivoire"
                    : "bg-obsidian-deep/40 text-titane/65 hover:bg-obsidian/60",
                )}
              >
                <button
                  type="button"
                  className="flex min-w-0 flex-1 items-center gap-1.5 truncate text-left"
                  onClick={() => onSelectTab(tab.path)}
                >
                  {tab.dirty ? (
                    <Circle className="h-2 w-2 shrink-0 fill-bronze text-bronze" />
                  ) : null}
                  <span className="truncate">{fileName(tab.path)}</span>
                </button>
                <button
                  type="button"
                  className="rounded p-0.5 opacity-0 transition-opacity hover:bg-obsidian-3 group-hover:opacity-100"
                  onClick={(e) => {
                    e.stopPropagation();
                    onCloseTab(tab.path);
                  }}
                  aria-label="Fermer"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            );
          })}
        </div>
      ) : null}

      <div className="min-h-0 flex-1">
        {active ? (
          <MonacoEditor
            height="100%"
            language={active.language}
            value={active.content}
            theme={ALNUA_MONACO_THEME}
            options={{
              ...MONACO_EDITOR_OPTIONS,
              readOnly: active.readOnly,
            }}
            beforeMount={registerAlnuaMonacoTheme}
            onChange={(v) => onChangeContent(active.path, v ?? "")}
            onMount={(editor) => {
              editor.onDidChangeCursorPosition((e) => {
                onCursorChange(e.position.lineNumber, e.position.column);
              });
            }}
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-6 p-8 text-center">
            <div className="space-y-2">
              <p className="font-title text-lg text-ivoire">ALNUA IDE</p>
              <p className="max-w-sm text-sm text-titane/60">
                Ouvre un fichier dans l&apos;explorateur ou utilise{" "}
                <kbd className="rounded border border-bronze-faint px-1.5 py-0.5 font-mono text-[10px] text-titane/70">
                  Ctrl+P
                </kbd>
              </p>
            </div>
            <div className="grid gap-2 text-left font-mono text-[11px] text-titane/50">
              <p>
                <kbd className="text-titane/70">Ctrl+S</kbd> Enregistrer
              </p>
              <p>
                <kbd className="text-titane/70">Ctrl+`</kbd> Terminal
              </p>
              <p>
                <kbd className="text-titane/70">Ctrl+B</kbd> Sidebar
              </p>
              <p>
                <kbd className="text-titane/70">Ctrl+L</kbd> Assistant IA
              </p>
            </div>
            <p className="text-[11px] text-titane/40">
              Ln {cursorLine}, Col {cursorCol}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

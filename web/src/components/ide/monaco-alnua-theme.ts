import type { Monaco } from "@monaco-editor/react";

/** ALNUA obsidian + bronze palette for Monaco (Cursor-like dark). */
export const ALNUA_MONACO_THEME = "alnua-dark";

export function registerAlnuaMonacoTheme(monaco: Monaco) {
  monaco.editor.defineTheme(ALNUA_MONACO_THEME, {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "comment", foreground: "6a7380", fontStyle: "italic" },
      { token: "keyword", foreground: "b87333" },
      { token: "string", foreground: "9ec89a" },
      { token: "number", foreground: "cf8d50" },
      { token: "type", foreground: "7eb8da" },
      { token: "function", foreground: "e8c4a8" },
    ],
    colors: {
      "editor.background": "#0E1014",
      "editor.foreground": "#e8e4dc",
      "editorLineNumber.foreground": "#4a5058",
      "editorLineNumber.activeForeground": "#A7ADB5",
      "editor.selectionBackground": "#E09B6A33",
      "editor.lineHighlightBackground": "#14171C",
      "editorCursor.foreground": "#F0C4A0",
      "editorIndentGuide.background": "#1C2027",
      "editorIndentGuide.activeBackground": "#2a3038",
      "editorWidget.background": "#14171C",
      "editorWidget.border": "#E09B6A33",
      "minimap.background": "#0E1014",
      "scrollbarSlider.background": "#E09B6A22",
      "scrollbarSlider.hoverBackground": "#E09B6A44",
    },
  });
}

export const MONACO_EDITOR_OPTIONS = {
  fontFamily: "var(--font-geist-mono), JetBrains Mono, ui-monospace, monospace",
  fontSize: 13,
  lineHeight: 20,
  fontLigatures: true,
  minimap: { enabled: true, scale: 1 },
  wordWrap: "off" as const,
  automaticLayout: true,
  smoothScrolling: true,
  cursorBlinking: "smooth" as const,
  cursorSmoothCaretAnimation: "on" as const,
  renderLineHighlight: "all" as const,
  bracketPairColorization: { enabled: true },
  padding: { top: 10, bottom: 10 },
  scrollBeyondLastLine: false,
  folding: true,
  glyphMargin: true,
  renderWhitespace: "selection" as const,
  suggestOnTriggerCharacters: true,
  quickSuggestions: true,
  tabSize: 2,
};

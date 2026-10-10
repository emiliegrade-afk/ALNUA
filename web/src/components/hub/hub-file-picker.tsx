"use client";

import { useCallback, useEffect, useState } from "react";
import { Paperclip, Trash2, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  deleteHubFile,
  listHubFiles,
  uploadHubFile,
  type HubFileSource,
  type HubUserFile,
} from "@/lib/hub-files-api";

interface Props {
  source: HubFileSource;
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  maxFiles?: number;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} o`;
  return `${(n / 1024).toFixed(1)} Ko`;
}

/** Pick or upload text files from the Hub library (Lot 1–2). */
export function HubFilePicker({ source, selectedIds, onChange, maxFiles = 5 }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [files, setFiles] = useState<HubUserFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setFiles(await listHubFiles({ q: query, source, limit: 80 }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chargement impossible.");
    } finally {
      setLoading(false);
    }
  }, [query, source]);

  useEffect(() => {
    if (!open) return;
    void refresh();
  }, [open, refresh]);

  useEffect(() => {
    if (selectedIds.length === 0) return;
    void listHubFiles({ source, limit: 200 }).then((all) => {
      setFiles((prev) => {
        const byId = new Map(prev.map((f) => [f.id, f]));
        for (const f of all) byId.set(f.id, f);
        return [...byId.values()].sort((a, b) => b.created_at.localeCompare(a.created_at));
      });
    });
  }, [selectedIds, source]);

  function toggle(id: string) {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((x) => x !== id));
      return;
    }
    if (selectedIds.length >= maxFiles) return;
    onChange([...selectedIds, id]);
  }

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setError(null);
    try {
      const meta = await uploadHubFile(file, source);
      await refresh();
      if (!selectedIds.includes(meta.id) && selectedIds.length < maxFiles) {
        onChange([...selectedIds, meta.id]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload impossible.");
    }
  }

  async function onDelete(fileId: string) {
    setError(null);
    try {
      await deleteHubFile(fileId);
      onChange(selectedIds.filter((id) => id !== fileId));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Suppression impossible.");
    }
  }

  const selectedMeta = files.filter((f) => selectedIds.includes(f.id));

  return (
    <div className="space-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              <Paperclip />
              Bibliothèque
            </Button>
          </DialogTrigger>
          <DialogContent className="max-h-[80vh] overflow-y-auto border-copper/20 bg-obsidian text-ivory">
            <DialogHeader>
              <DialogTitle>Fichiers Hub</DialogTitle>
            </DialogHeader>
            <div className="flex gap-2">
              <Input
                placeholder="Rechercher…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void refresh()}
              />
              <Button type="button" variant="secondary" onClick={() => void refresh()}>
                OK
              </Button>
            </div>
            <label className="flex cursor-pointer items-center gap-2 text-sm text-copper-light">
              <Upload className="size-4" />
              Ajouter un fichier texte
              <input type="file" className="hidden" accept=".txt,.md,.json,.csv,.log,.yaml,.yml" onChange={onUpload} />
            </label>
            {loading && <p className="text-xs text-muted-foreground">Chargement…</p>}
            {error && (
              <p role="alert" className="text-xs text-red-400">
                {error}
              </p>
            )}
            <ul className="space-y-1 text-sm">
              {files.map((f) => (
                <li
                  key={f.id}
                  className="flex items-center justify-between gap-2 rounded-lg border border-copper/15 px-2 py-1"
                >
                  <button
                    type="button"
                    className="min-w-0 flex-1 truncate text-left hover:text-copper-light"
                    onClick={() => toggle(f.id)}
                  >
                    {selectedIds.includes(f.id) ? "✓ " : ""}
                    {f.name} ({formatBytes(f.size_bytes)})
                  </button>
                  <Button type="button" variant="ghost" size="icon-sm" onClick={() => void onDelete(f.id)}>
                    <Trash2 className="size-3.5" />
                  </Button>
                </li>
              ))}
            </ul>
          </DialogContent>
        </Dialog>
        {selectedMeta.map((f) => (
          <span
            key={f.id}
            className="rounded-full border border-copper/25 bg-obsidian-2 px-2 py-0.5 text-xs text-ivory"
          >
            {f.name}
          </span>
        ))}
      </div>
    </div>
  );
}

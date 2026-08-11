"use client";

import { useCallback, useEffect, useState } from "react";
import { HardDrive, Loader2, NotebookPen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  createNadiaDoc,
  housekeeperApply,
  housekeeperPropose,
  housekeeperScan,
  housekeeperStatus,
  listNadiaDocs,
  type HousekeeperStatus,
  type NadiaDocMeta,
} from "@/lib/nadia-tools-api";
import { toast } from "sonner";

export function NadiaToolsPanel() {
  const [docs, setDocs] = useState<NadiaDocMeta[]>([]);
  const [hk, setHk] = useState<HousekeeperStatus | null>(null);
  const [log, setLog] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("Note Nadia");

  const refresh = useCallback(async () => {
    try {
      const [d, s] = await Promise.all([listNadiaDocs(), housekeeperStatus()]);
      setDocs(d.documents.slice(0, 8));
      setHk(s);
    } catch {
      /* hub offline */
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function newDoc() {
    setBusy(true);
    try {
      const doc = await createNadiaDoc({
        title: title.trim() || "Note Nadia",
        content: `# ${title.trim() || "Note"}\n\n`,
        doc_type: "note",
      });
      toast.success(`Doc créé : ${doc.id}`);
      await refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Création impossible");
    } finally {
      setBusy(false);
    }
  }

  async function run(label: string, fn: () => Promise<Record<string, unknown>>) {
    setBusy(true);
    setLog(null);
    try {
      const res = await fn();
      setLog(JSON.stringify(res, null, 2));
      await refresh();
      toast.success(label);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : label);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="border-copper/30 bg-transparent">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
            <NotebookPen className="h-4 w-4 text-copper" />
            Documents Nadia
          </CardTitle>
          <p className="label-caps">Word (.docx) pour contrats · notes md</p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <input
              className="flex-1 rounded border border-copper/20 bg-obsidian-1 px-3 py-1.5 text-sm text-ivory"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <Button type="button" size="sm" disabled={busy} onClick={() => void newDoc()}>
              Créer
            </Button>
          </div>
          <ul className="space-y-1 text-xs text-titanium/80">
            {docs.length === 0 && <li>Aucun document encore.</li>}
            {docs.map((d) => (
              <li key={d.id}>
                <span className="text-ivory">{d.title}</span>{" "}
                <span className="text-titanium/50">({d.id})</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card className="border-copper/30 bg-transparent">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
            <HardDrive className="h-4 w-4 text-copper" />
            Clara — Ménage PC
          </CardTitle>
          <p className="label-caps">
            Quarantaine avant suppression · {hk?.quarantine_count ?? 0} en file
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-titanium/70">
            Racines : {(hk?.roots || []).join(" · ") || "Desktop / Documents / Downloads"}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() => void run("Scan", () => housekeeperScan())}
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Scan"}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() => void run("Proposition", () => housekeeperPropose())}
            >
              Proposer
            </Button>
            <Button
              type="button"
              size="sm"
              disabled={busy}
              onClick={() => void run("Déplacements", () => housekeeperApply(false))}
            >
              Appliquer
            </Button>
          </div>
          {log && (
            <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-obsidian-1 p-2 text-[11px] text-ivory/80">
              {log}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

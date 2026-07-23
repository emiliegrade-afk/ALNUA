"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Shield, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  applyLibraryRetention,
  fetchLibraryRetentionPreview,
  type LibraryRetentionPreview,
} from "@/lib/library-api";

export function LibraryRetentionCard({ onApplied }: { onApplied?: () => void }) {
  const [preview, setPreview] = useState<LibraryRetentionPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchLibraryRetentionPreview();
      setPreview(data);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Aperçu garde-fou indisponible",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleApply(dryRun: boolean) {
    setBusy(true);
    try {
      const res = await applyLibraryRetention({ dry_run: dryRun });
      const msg = String(res.message ?? "Terminé");
      if (dryRun) {
        toast.message(msg);
      } else {
        toast.success(msg);
        onApplied?.();
        await load();
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Garde-fou échoué");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="mb-8 border-bronze-faint bg-obsidian-2/90">
      <CardHeader className="space-y-1">
        <CardTitle className="flex items-center gap-2 font-title text-base text-ivoire">
          <Shield className="h-4 w-4 text-bronze-bright" />
          Garde-fou bibliothèque
        </CardTitle>
        <p className="font-body text-xs text-titane/60">
          Compresse les fiches déjà apprises par tous les agents (archives légères).
          Supprime doublons, résumés vides et fiches « à garder » jamais utilisées
          depuis 180 jours.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && !preview ? (
          <p className="flex items-center gap-2 text-sm text-titane/50">
            <Loader2 className="h-4 w-4 animate-spin" />
            Analyse…
          </p>
        ) : preview ? (
          <>
            <p className="text-sm text-titane/75">{preview.message}</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-3 text-center">
                <p className="font-mono text-lg text-ivoire">
                  {preview.compress_candidates}
                </p>
                <p className="text-[10px] text-titane/50">à compresser</p>
              </div>
              <div className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-3 text-center">
                <p className="font-mono text-lg text-amber-300">
                  {preview.purge_candidates}
                </p>
                <p className="text-[10px] text-titane/50">à purger</p>
              </div>
              <div className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-3 text-center">
                <p className="font-mono text-lg text-titane/70">
                  {preview.archives_count}
                </p>
                <p className="text-[10px] text-titane/50">archives</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                className="border-bronze-faint text-xs"
                disabled={busy}
                onClick={() => void handleApply(true)}
              >
                Simuler
              </Button>
              <Button
                size="sm"
                className="gap-1.5 bg-bronze text-obsidian hover:bg-bronze-bright"
                disabled={busy}
                onClick={() => void handleApply(false)}
              >
                {busy ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
                Appliquer le nettoyage
              </Button>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

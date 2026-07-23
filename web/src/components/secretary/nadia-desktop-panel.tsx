"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Monitor, Power } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchNadiaDesktopStatus,
  registerNadiaBoot,
  type NadiaDesktopStatus,
} from "@/lib/nadia-desktop-api";
import { toast } from "sonner";

export function NadiaDesktopPanel() {
  const [status, setStatus] = useState<NadiaDesktopStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [booting, setBooting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setStatus(await fetchNadiaDesktopStatus());
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleBoot() {
    setBooting(true);
    try {
      const res = await registerNadiaBoot();
      toast.success("Session PC enregistrée");
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              last_boot_at: res.boot_at,
              boot_count: res.boot_count,
              greeting_preview: res.greeting,
              hub: res.hub,
            }
          : null
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Hub injoignable");
    } finally {
      setBooting(false);
    }
  }

  return (
    <Card className="mb-8 border-copper/30 bg-obsidian-2/90">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
          <Monitor className="h-4 w-4 text-copper" />
          Nadia — compagnon PC
        </CardTitle>
        <p className="label-caps">
          Pont entre toi, ton PC et le Hub · voix bientôt
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-titanium/60">
            <Loader2 className="h-4 w-4 animate-spin" />
            Connexion au Hub…
          </div>
        ) : status ? (
          <>
            <p className="text-xs text-titanium/70">
              Hub API{" "}
              {status.hub.online ? (
                <span className="text-emerald-400">● en ligne</span>
              ) : (
                <span className="text-amber-400">● hors ligne — lance Demarrer-Hub.bat</span>
              )}
              {status.last_boot_at ? (
                <span className="ml-2">
                  · dernière session {new Date(status.last_boot_at).toLocaleString("fr-FR")}
                </span>
              ) : null}
            </p>
            <pre className="whitespace-pre-wrap rounded-lg border border-white/10 bg-obsidian/60 p-3 font-body text-sm text-ivory/90">
              {status.greeting_preview}
            </pre>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={booting}
                onClick={() => void handleBoot()}
              >
                {booting ? (
                  <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                ) : (
                  <Power className="mr-2 h-3 w-3" />
                )}
                Accueil session PC
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="text-titanium/60"
                onClick={() => void load()}
              >
                Actualiser
              </Button>
            </div>
            <p className="text-[11px] text-titanium/50">
              Auto au démarrage Windows :{" "}
              <code className="text-copper/80">scripts\install-nadia-startup.ps1</code>
            </p>
          </>
        ) : (
          <p className="text-sm text-titanium/60">
            Hub injoignable — démarre ALNUA puis reviens ici.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

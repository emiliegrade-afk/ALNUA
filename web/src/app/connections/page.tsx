"use client";

import { useCallback, useEffect, useState } from "react";
import { ExternalLink, Loader2, Plug } from "lucide-react";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  connectComposioApp,
  fetchComposioApps,
  type ComposioApp,
} from "@/lib/composio-api";
import { toast } from "sonner";

const SUGGESTED_APPS = ["GMAIL", "GITHUB", "SLACK", "NOTION", "DISCORD"];

export default function ConnectionsPage() {
  const [apps, setApps] = useState<ComposioApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchComposioApps();
      setApps(data);
    } catch {
      setApps([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleConnect(appName: string) {
    setConnecting(appName);
    try {
      const { oauth_url } = await connectComposioApp(appName);
      window.open(oauth_url, "_blank", "noopener,noreferrer");
      toast.success(`Lien OAuth ouvert pour ${appName}`);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Connexion impossible"
      );
    } finally {
      setConnecting(null);
    }
  }

  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="it"
        title="IT / Connexions"
        subtitle="Apps OAuth · Composio · Intégrations"
      />

      <Card className="mb-8 border-copper-dim/30 bg-obsidian-2/90">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
            <Plug className="h-4 w-4 text-copper-dim" />
            Apps connectées
          </CardTitle>
          <p className="label-caps">
            {apps.length} app{apps.length !== 1 ? "s" : ""} via Composio
          </p>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 font-body text-sm text-titanium/60">
              <Loader2 className="h-4 w-4 animate-spin" />
              Chargement…
            </div>
          ) : apps.length === 0 ? (
            <p className="font-body text-sm text-titanium/60">
              Aucune app connectée. Utilise les boutons ci-dessous pour
              connecter Gmail, GitHub, etc.
            </p>
          ) : (
            <ul className="space-y-2">
              {apps.map((app) => (
                <li
                  key={app.app}
                  className="flex items-center justify-between rounded-lg border border-copper/10 px-4 py-3"
                >
                  <span className="font-body text-sm text-ivory">{app.app}</span>
                  <span className="badge-copper px-2 py-0.5 text-xs">
                    {app.status ?? "connecté"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <section>
        <h2 className="mb-4 text-sm font-medium uppercase tracking-widest text-gray-500">
          Connecter une app
        </h2>
        <div className="flex flex-wrap gap-3">
          {SUGGESTED_APPS.map((app) => (
            <Button
              key={app}
              variant="outline"
              className="border-gray-500/30"
              disabled={connecting === app}
              onClick={() => handleConnect(app)}
            >
              {connecting === app ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <ExternalLink className="mr-2 h-4 w-4" />
              )}
              {app}
            </Button>
          ))}
        </div>
      </section>
    </>
  );
}

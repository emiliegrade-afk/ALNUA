"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Plug,
  LineChart,
  RefreshCw,
} from "lucide-react";
import { BureauPage } from "@/components/shared/bureau-page";
import { BureauPanel } from "@/components/shared/bureau-panel";
import { Button } from "@/components/ui/button";
import {
  connectComposioApp,
  fetchComposioApps,
  type ComposioApp,
} from "@/lib/composio-api";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { toast } from "sonner";

const SUGGESTED_APPS = ["GMAIL", "GITHUB", "SLACK", "NOTION", "DISCORD"];

export default function ConnectionsPage() {
  const { phase: hubPhase } = useHubHealthLive();
  const [apps, setApps] = useState<ComposioApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await fetchComposioApps();
      setApps(data);
    } catch (err) {
      setApps([]);
      setLoadError(
        err instanceof Error ? err.message : "Impossible de charger les connexions Composio.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleConnect(appName: string) {
    if (hubPhase !== "ok") {
      toast.error("API Hub hors ligne — démarre le backend avant de connecter une app.");
      return;
    }
    setConnecting(appName);
    try {
      const { oauth_url } = await connectComposioApp(appName);
      window.open(oauth_url, "_blank", "noopener,noreferrer");
      toast.success(`Lien OAuth ouvert pour ${appName}`);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Connexion impossible",
      );
    } finally {
      setConnecting(null);
    }
  }

  const hubOnline = hubPhase === "ok";
  const hubChecking = hubPhase === "checking";

  return (
    <BureauPage
      dept="it"
      title="IT / Connexions"
      subtitle="Gmail · GitHub OAuth · Composio (pas tes projets de code)"
    >
      <BureauPanel title="État du Hub" icon={hubOnline ? CheckCircle2 : AlertTriangle}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p
              className={
                hubOnline
                  ? "text-sm text-bronze-bright"
                  : hubChecking
                    ? "text-sm text-titane/70"
                    : "text-sm text-red-400"
              }
            >
              {hubOnline
                ? "API Hub connectée — prêt pour OAuth Composio"
                : hubChecking
                  ? "Vérification de l'API Hub…"
                  : "API Hub hors ligne — la page ne peut pas charger les connexions"}
            </p>
            {!hubOnline && !hubChecking ? (
              <p className="mt-1 text-xs text-titane/55">
                Lance{" "}
                <code className="rounded bg-obsidian-deep/70 px-1 py-0.5">
                  scripts\restart_hub_api.ps1
                </code>{" "}
                puis recharge cette page.
              </p>
            ) : null}
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="border-bronze-faint"
            disabled={loading}
            onClick={() => void load()}
          >
            <RefreshCw className={`mr-2 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Actualiser
          </Button>
        </div>
      </BureauPanel>

      <p className="rounded-xl border border-bronze-faint bg-obsidian/70 px-4 py-3 font-body text-sm text-titane/80">
        Ce n&apos;est pas la page pour lier Naïa ou créer une app. Pour tes repos
        et l&apos;App Factory, va sur{" "}
        <Link href="/apps" className="text-bronze-bright underline hover:text-ivoire">
          Mes apps
        </Link>
        .
      </p>

      <BureauPanel title="Apps connectées" icon={Plug}>
        <p className="label-caps mb-4">
          {apps.length} app{apps.length !== 1 ? "s" : ""} via Composio
        </p>
        {loading ? (
          <div className="flex items-center gap-2 font-body text-sm text-titane/60">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement…
          </div>
        ) : loadError ? (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {loadError}
          </div>
        ) : apps.length === 0 ? (
          <p className="font-body text-sm text-titane/60">
            Aucune app connectée. Utilise les boutons ci-dessous pour
            connecter Gmail, GitHub, etc.
          </p>
        ) : (
          <ul className="space-y-2">
            {apps.map((app) => (
              <li
                key={app.app}
                className="flex items-center justify-between rounded-lg border border-bronze-faint bg-obsidian-deep/50 px-4 py-3"
              >
                <span className="font-body text-sm text-ivoire">{app.app}</span>
                <span className="rounded-full border border-bronze-faint bg-bronze/10 px-2 py-0.5 text-xs text-bronze-bright">
                  {app.status ?? "connecté"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </BureauPanel>

      <BureauPanel title="Langfuse — Monitoring agents" icon={LineChart}>
        <p className="label-caps mb-4">Traces LLM, coûts et latence en temps réel</p>
        <a
          href="https://cloud.langfuse.com"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg border border-bronze-faint bg-obsidian-deep/50 px-4 py-3 font-body text-sm text-ivoire transition-colors hover:border-bronze/40 hover:bg-obsidian/80"
        >
          <ExternalLink className="h-4 w-4 text-bronze" />
          Ouvrir le dashboard Langfuse
        </a>
      </BureauPanel>

      <section>
        <h2 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-titane/55">
          Connecter une app
        </h2>
        <div className="flex flex-wrap gap-3">
          {SUGGESTED_APPS.map((app) => (
            <Button
              key={app}
              type="button"
              variant="outline"
              className="border-bronze-faint"
              disabled={connecting === app || !hubOnline}
              onClick={() => void handleConnect(app)}
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
    </BureauPage>
  );
}

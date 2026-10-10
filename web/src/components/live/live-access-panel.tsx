"use client";

import { useCallback, useEffect, useState } from "react";
import { Globe, Mail, CalendarDays, MessageCircle, Camera, Briefcase } from "lucide-react";

import { Button } from "@/components/ui/button";
import { connectLiveApp, toLiveAccess, type LiveAccess, type LiveAppAccess } from "@/lib/live-api";
import { fillOAuthPopup } from "@/lib/live-oauth";
import { cn } from "@/lib/utils";

const ROWS: { key: keyof LiveAccess["ready"]; label: string; app?: string; Icon: typeof Globe }[] = [
  { key: "research", label: "Internet", Icon: Globe },
  { key: "mail", label: "Gmail", app: "gmail", Icon: Mail },
  { key: "calendar", label: "Agenda", app: "googlecalendar", Icon: CalendarDays },
  { key: "discord", label: "Discord", app: "discord", Icon: MessageCircle },
  { key: "instagram", label: "Instagram", app: "instagram", Icon: Camera },
  { key: "linkedin", label: "LinkedIn", app: "linkedin", Icon: Briefcase },
];

function caption(key: keyof LiveAccess["ready"], access: LiveAccess): string {
  if (key === "research") return access.internet.detail || (access.ready.research ? "OK" : "hors ligne");
  const app = access.apps[key === "mail" ? "gmail" : key === "calendar" ? "googlecalendar" : key];
  return appCaption(app);
}

function appCaption(app: LiveAppAccess | undefined): string {
  if (!app) return "inconnu";
  if (app.account && app.account_ok === false) return `${app.account} — mauvais compte`;
  if (app.account) return app.account;
  if (app.detail) return app.detail;
  if (app.ok) return app.via === "bot" ? "bot (annonces)" : "connecté";
  return "à connecter";
}

export function LiveAccessPanel() {
  const [access, setAccess] = useState<LiveAccess | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<{ app: string; url: string; hint: string } | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch(`/api/hub/live/access?t=${Date.now()}`, { cache: "no-store" });
      if (!res.ok) {
        throw new Error(`Hub ${res.status} — relance le Hub si ça dure.`);
      }
      const raw = (await res.json()) as Record<string, unknown>;
      setAccess(toLiveAccess(raw));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Accès illisibles.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const connect = async (app: string, popup: Window | null) => {
    setError(null);
    setBusy(app);
    try {
      const { url, hint } = await connectLiveApp(app);
      setPending({ app, url, hint });
      if (!fillOAuthPopup(popup, url)) {
        setError("Le navigateur a bloqué la fenêtre. Clique le lien ci-dessous.");
      }
      await refresh();
    } catch (err) {
      popup?.close();
      setError(err instanceof Error ? err.message : "Connexion impossible.");
    } finally {
      setBusy(null);
    }
  };

  return (
    <section aria-label="Accès Nadia" className="rounded-xl border border-copper/20 bg-obsidian-2 p-3">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-copper-light">Accès</h2>
        <Button variant="ghost" size="sm" onClick={() => void refresh()}>
          Vérifier
        </Button>
      </div>
      <ul className="grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {ROWS.map(({ key, label, app, Icon }) => {
          const ok = access?.ready[key] === true;
          return (
            <li key={key} className="flex flex-col gap-1 rounded-lg border border-copper/10 p-2">
              <span className="flex items-center gap-1.5 text-sm text-ivory">
                <Icon className="size-3.5 text-copper-light" />
                {label}
                <span
                  className={cn(
                    "ml-auto size-2 rounded-full",
                    ok ? "bg-emerald-400" : "bg-zinc-500",
                  )}
                  aria-label={ok ? "prêt" : "manquant"}
                />
              </span>
              <span className="truncate text-[11px] text-zinc-400">
                {access ? caption(key, access) : error ? "échec" : "…"}
              </span>
              {app && access && !ok ? (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={busy === app}
                  onClick={() => {
                    const popup = window.open("about:blank", "_blank");
                    void connect(app, popup);
                  }}
                >
                  Connecter
                </Button>
              ) : null}
            </li>
          );
        })}
      </ul>
      {pending ? (
        <p className="mt-2 text-xs text-ivory/80">
          {pending.hint ? `${pending.hint} — ` : null}
          <a
            href={pending.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-copper-light underline"
          >
            Ouvrir {pending.app}
          </a>
        </p>
      ) : null}
      <p className="mt-2 text-[11px] leading-relaxed text-zinc-500">
        Gmail : autorise <span className="text-zinc-300">alnua.global@gmail.com</span>.
        Instagram : Meta n&apos;accepte qu&apos;un compte <span className="text-zinc-300">Professionnel</span>{" "}
        lié à une Page Facebook — un compte perso est refusé. Après OAuth, clique Vérifier.
        Pour juste ouvrir le site : dis « ouvre Instagram ».
      </p>
      {error ? <p className="mt-2 text-xs text-red-300">{error}</p> : null}
    </section>
  );
}

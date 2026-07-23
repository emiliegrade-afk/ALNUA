"use client";

import { useCallback, useEffect, useState } from "react";
import { FolderGit2, Loader2, Plus, Trash2 } from "lucide-react";
import { BureauPage } from "@/components/shared/bureau-page";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  deleteAppRegistry,
  fetchAppRegistry,
  upsertAppRegistry,
  type AppBranch,
  type AppRegistryEntry,
} from "@/lib/apps-api";
import { AppFactoryPanel } from "@/components/apps/app-factory-panel";
import { toast } from "sonner";

const BRANCHES: AppBranch[] = ["hub", "app", "gaming", "robotics", "other"];

const EMPTY_FORM = {
  slug: "",
  name: "",
  branch: "app" as AppBranch,
  github_repo: "",
  local_path: "",
  description: "",
  stack: "",
  prod_url: "",
};

export default function AppsPage() {
  const [apps, setApps] = useState<AppRegistryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchAppRegistry();
      setApps(data.apps);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Impossible de charger les apps"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!form.slug.trim() || !form.name.trim()) {
      toast.error("Slug et nom requis");
      return;
    }
    setSaving(true);
    try {
      await upsertAppRegistry({
        ...form,
        slug: form.slug.trim(),
        name: form.name.trim(),
      });
      toast.success("App enregistrée");
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur enregistrement");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(slug: string) {
    try {
      await deleteAppRegistry(slug);
      toast.success("Entrée registry supprimée");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Suppression impossible");
    }
  }

  return (
    <BureauPage
      dept="it"
      title="Mes apps"
      subtitle="Repos locaux · GitHub · pôles App / Gaming / Robotique"
    >
      <AppFactoryPanel onRegistered={() => void load()} />

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_22rem]">
        <Card className="border-copper-dim/30 bg-obsidian-2/90">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
              <FolderGit2 className="h-4 w-4 text-copper-dim" />
              Apps liées au Hub
            </CardTitle>
            <p className="label-caps">
              Les repos .env sont fusionnés avec ce registre
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-titanium/60">
                <Loader2 className="h-4 w-4 animate-spin" />
                Chargement…
              </div>
            ) : apps.length === 0 ? (
              <p className="text-sm text-titanium/60">
                Aucune app — lance la factory ou ajoute un projet à droite.
              </p>
            ) : (
              <ul className="space-y-3">
                {apps.map((app) => (
                  <li
                    key={app.slug}
                    className="rounded-lg border border-white/10 bg-obsidian/60 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-title text-sm text-ivory">
                          {app.name}{" "}
                          <span className="text-titanium/50">({app.slug})</span>
                        </p>
                        <p className="mt-1 text-xs text-copper/80">{app.branch}</p>
                        {app.local_path ? (
                          <p className="mt-1 break-all font-mono text-[11px] text-titanium/70">
                            {app.local_path}
                            {app.path_exists ? (
                              <span className="ml-2 text-emerald-400">● local OK</span>
                            ) : (
                              <span className="ml-2 text-red-400">● chemin absent</span>
                            )}
                          </p>
                        ) : null}
                        {app.github_repo ? (
                          <p className="mt-1 font-mono text-[11px] text-titanium/60">
                            {app.github_repo}
                          </p>
                        ) : null}
                        <p className="mt-1 text-[10px] uppercase tracking-wide text-titanium/40">
                          source: {app.source}
                        </p>
                      </div>
                      {app.source === "registry" || app.source === "merged" ? (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="shrink-0 text-titanium/50 hover:text-red-300"
                          onClick={() => void handleDelete(app.slug)}
                          aria-label={`Supprimer ${app.slug}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="border-copper-dim/30 bg-obsidian-2/90">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
              <Plus className="h-4 w-4 text-copper-dim" />
              Lier une app
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={handleSave}>
              <div>
                <Label htmlFor="slug">Slug</Label>
                <Input
                  id="slug"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  placeholder="mon-app"
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="name">Nom</Label>
                <Input
                  id="name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Mon App"
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="branch">Pôle</Label>
                <select
                  id="branch"
                  value={form.branch}
                  onChange={(e) =>
                    setForm({ ...form, branch: e.target.value as AppBranch })
                  }
                  className="mt-1 w-full rounded-md border border-white/10 bg-obsidian px-3 py-2 text-sm text-ivory"
                >
                  {BRANCHES.map((b) => (
                    <option key={b} value={b}>
                      {b}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="local_path">Chemin local</Label>
                <Input
                  id="local_path"
                  value={form.local_path}
                  onChange={(e) =>
                    setForm({ ...form, local_path: e.target.value })
                  }
                  placeholder="C:\Dev\mon-app"
                  className="mt-1 font-mono text-xs"
                />
              </div>
              <div>
                <Label htmlFor="github_repo">GitHub (owner/repo)</Label>
                <Input
                  id="github_repo"
                  value={form.github_repo}
                  onChange={(e) =>
                    setForm({ ...form, github_repo: e.target.value })
                  }
                  placeholder="emiliegrade-afk/mon-app"
                  className="mt-1 font-mono text-xs"
                />
              </div>
              <div>
                <Label htmlFor="stack">Stack</Label>
                <Input
                  id="stack"
                  value={form.stack}
                  onChange={(e) => setForm({ ...form, stack: e.target.value })}
                  placeholder="Next.js, Expo…"
                  className="mt-1"
                />
              </div>
              <Button type="submit" disabled={saving} className="w-full">
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Enregistrement…
                  </>
                ) : (
                  "Enregistrer"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </BureauPage>
  );
}

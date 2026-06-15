"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ADMIN_LINKS,
  fetchAdminFlags,
  isAdminPageEnabled,
  withAdminPreview,
  type AdminFlags,
} from "@/lib/admin-flags-api";

export default function AdminHubPage() {
  const [flags, setFlags] = useState<AdminFlags | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewMode, setPreviewMode] = useState(false);

  useEffect(() => {
    setPreviewMode(
      new URLSearchParams(window.location.search).get("preview") === "1"
    );
    fetchAdminFlags()
      .then(setFlags)
      .catch(() => setFlags(null))
      .finally(() => setLoading(false));
  }, []);

  const visible = ADMIN_LINKS.filter((link) =>
    isAdminPageEnabled(flags, link.flag, previewMode)
  );

  return (
    <div className="mx-auto max-w-3xl pb-16">
      <header className="mb-8">
        <p className="label-caps mb-2 text-copper/80">Admin</p>
        <h1 className="font-title text-2xl text-ivory">Outils Tier 3</h1>
        <p className="mt-2 font-body text-sm text-titanium/70">
          Services avancés — accessibles quand les flags sont activés côté API.
        </p>
        {previewMode && flags?.preview_allowed ? (
          <p className="mt-2 font-body text-xs text-copper/80">
            Mode prévisualisation actif (?preview=1)
          </p>
        ) : null}
      </header>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-copper/60" />
        </div>
      ) : visible.length === 0 ? (
        <Card className="border-copper/20 bg-obsidian-2/80">
          <CardContent className="p-6 font-body text-sm text-titanium/70">
            Aucun outil admin activé. Définis{" "}
            <code className="text-copper-light">ADMIN_*_PAGE_ENABLED=1</code> dans
            ton <code>.env</code> API.
            {flags?.preview_allowed && (
              <p className="mt-3 text-xs">
                Dev :{" "}
                <Link
                  href="/admin?preview=1"
                  className="text-copper-light underline-offset-2 hover:underline"
                >
                  ouvre cette page avec ?preview=1
                </Link>
              </p>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {visible.map((link) => (
            <Link key={link.href} href={withAdminPreview(link.href, previewMode)}>
              <Card className="border-copper/20 bg-obsidian-2/80 transition hover:border-copper/40">
                <CardHeader>
                  <CardTitle className="font-title text-base text-ivory">
                    {link.label}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0 font-body text-xs text-titanium/50">
                  {withAdminPreview(link.href, previewMode)}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

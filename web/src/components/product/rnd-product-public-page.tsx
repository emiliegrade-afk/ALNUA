"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Check, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  fetchPublicProductPage,
  type RndProductPage,
} from "@/lib/rnd-dossier";
import { hubPublicApiUrl } from "@/lib/hub-api-config";
import { joinWaitlist } from "@/lib/waitlist-api";
import { cn } from "@/lib/utils";

interface RndProductPublicPageProps {
  slug: string;
}

function resolveHeroUrl(page: RndProductPage): string | null {
  if (!page.hero_url) return null;
  if (page.hero_url.startsWith("http")) return page.hero_url;
  return hubPublicApiUrl(page.hero_url);
}

export function RndProductPublicPage({ slug }: RndProductPublicPageProps) {
  const [page, setPage] = useState<RndProductPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [joined, setJoined] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setPage(await fetchPublicProductPage(slug));
    } catch (e) {
      setPage(null);
      setError(e instanceof Error ? e.message : "Fiche introuvable");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleJoinWaitlist(e: React.FormEvent) {
    e.preventDefault();
    if (!page?.project_slug || !email.trim()) return;
    setSubmitting(true);
    try {
      await joinWaitlist({
        project_slug: page.project_slug,
        email: email.trim(),
        first_name: firstName.trim() || undefined,
        source: "product_page",
      });
      setJoined(true);
      toast.success("Inscription enregistrée — merci !");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Inscription impossible");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-obsidian">
        <Loader2 className="h-8 w-8 animate-spin text-copper/50" />
      </div>
    );
  }

  if (error || !page) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-obsidian px-6 text-center">
        <AlnuaLogo className="h-8 opacity-60" />
        <h1 className="font-title text-2xl text-ivory">Produit introuvable</h1>
        <p className="max-w-md text-sm text-titanium/60">
          {error ?? "Cette fiche n&apos;est pas publiée ou n&apos;existe pas."}
        </p>
        <Button asChild variant="outline" className="border-white/10">
          <Link href="/">Retour au Hub</Link>
        </Button>
      </div>
    );
  }

  const heroSrc = resolveHeroUrl(page);

  return (
    <div className="min-h-screen bg-obsidian text-ivory">
      <header className="border-b border-white/8 bg-obsidian-2/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link href="/" className="opacity-80 transition hover:opacity-100">
            <AlnuaLogo className="h-7" />
          </Link>
          {page.pricing_model ? (
            <span className="rounded-full border border-copper/30 bg-copper/10 px-3 py-1 text-xs text-copper">
              {page.pricing_model}
            </span>
          ) : null}
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden border-b border-copper/10">
          {heroSrc ? (
            <div className="absolute inset-0 opacity-30">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={heroSrc} alt="" className="h-full w-full object-cover" />
            </div>
          ) : null}
          <div className="relative mx-auto max-w-5xl px-6 py-16 sm:py-24">
            <p className="label-caps mb-3 text-copper/80">ALNUA — coming soon</p>
            <h1 className="font-title text-4xl font-medium leading-tight sm:text-5xl">
              {page.title}
            </h1>
            {page.tagline ? (
              <p className="mt-4 max-w-2xl text-lg leading-relaxed text-ivory/85">
                {page.tagline}
              </p>
            ) : null}
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-6 py-12">
          {page.description_html ? (
            <div
              className="prose prose-invert max-w-3xl prose-p:text-ivory/85 prose-headings:font-title prose-headings:text-ivory"
              dangerouslySetInnerHTML={{ __html: page.description_html }}
            />
          ) : null}
        </section>

        {page.features.length > 0 ? (
          <section className="border-y border-white/8 bg-white/[0.02] py-12">
            <div className="mx-auto grid max-w-5xl gap-4 px-6 sm:grid-cols-2">
              {page.features.map((f) => (
                <article
                  key={f.title}
                  className="rounded-2xl border border-copper/12 bg-obsidian-2/50 p-6"
                >
                  <h3 className="font-title text-lg text-ivory">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-titanium/75">
                    {f.description}
                  </p>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        {page.waitlist_enabled && page.project_slug ? (
          <section className="mx-auto max-w-xl px-6 py-16">
            {joined ? (
              <div className="rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-8 text-center">
                <Check className="mx-auto mb-3 h-10 w-10 text-emerald-400" />
                <h2 className="font-title text-xl text-ivory">Tu es sur la liste</h2>
                <p className="mt-2 text-sm text-titanium/70">
                  On te préviendra dès que {page.title} ouvre l&apos;accès early.
                </p>
              </div>
            ) : (
              <form
                onSubmit={(e) => void handleJoinWaitlist(e)}
                className="rounded-2xl border border-copper/20 bg-copper/[0.04] p-8"
              >
                <h2 className="font-title text-xl text-ivory">Rejoins la waitlist</h2>
                <p className="mt-2 text-sm text-titanium/70">
                  Accès anticipé — pas de spam, désinscription à tout moment.
                </p>
                <div className="mt-6 space-y-3">
                  <Input
                    type="text"
                    placeholder="Prénom (optionnel)"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="border-white/10 bg-obsidian/60"
                  />
                  <Input
                    type="email"
                    required
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="border-white/10 bg-obsidian/60"
                  />
                  <Button
                    type="submit"
                    disabled={submitting}
                    className="w-full bg-copper text-obsidian hover:bg-copper/90"
                  >
                    {submitting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      "M&apos;inscrire"
                    )}
                  </Button>
                </div>
              </form>
            )}
          </section>
        ) : null}

        {page.faq.length > 0 ? (
          <section className="mx-auto max-w-3xl px-6 pb-16">
            <h2 className="label-caps mb-6 text-titanium/50">Questions fréquentes</h2>
            <div className="space-y-4">
              {page.faq.map((item) => (
                <details
                  key={item.question}
                  className={cn(
                    "group rounded-xl border border-white/10 bg-white/[0.02] p-4",
                    "open:border-copper/20"
                  )}
                >
                  <summary className="cursor-pointer text-sm font-medium text-ivory/90">
                    {item.question}
                  </summary>
                  <p className="mt-3 text-sm leading-relaxed text-titanium/75">
                    {item.answer}
                  </p>
                </details>
              ))}
            </div>
          </section>
        ) : null}
      </main>

      <footer className="border-t border-white/8 py-8 text-center text-xs text-titanium/45">
        © ALNUA — {page.title}
      </footer>
    </div>
  );
}

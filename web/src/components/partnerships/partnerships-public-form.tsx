"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import {
  AUDIENCE_BUCKETS,
  PROJECT_OPTIONS,
  PUBLIC_REQUEST_TYPES,
} from "@/components/partnerships/partnerships.constants";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { submitPartnershipRequest } from "@/lib/partnerships-api";
import { cn } from "@/lib/utils";

export function PartnershipsPublicForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [type, setType] = useState<string>("influencer");
  const [projects, setProjects] = useState<string[]>([]);
  const [instagram, setInstagram] = useState("");
  const [tiktok, setTiktok] = useState("");
  const [website, setWebsite] = useState("");
  const [audience, setAudience] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const toggleProject = (p: string) => {
    setProjects((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitPartnershipRequest({
        name: name.trim(),
        email: email.trim(),
        type,
        message: message.trim() || undefined,
        instagram_url: instagram.trim() || undefined,
        tiktok_url: tiktok.trim() || undefined,
        website: website.trim() || undefined,
        audience_size: audience || undefined,
        project_interest: projects.length ? projects.join(", ") : undefined,
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Envoi impossible");
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-obsidian px-4 py-12">
        <AlnuaLogo variant="lockup" height={48} />
        <p className="mt-10 text-center text-xl text-ivory">
          Merci {name} ! On revient vers toi sous 48h. 💌
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-obsidian px-4 py-10 sm:py-14">
      <div className="mx-auto max-w-lg">
        <div className="mb-10 text-center">
          <AlnuaLogo variant="lockup" height={52} className="mx-auto" />
          <h1 className="mt-8 text-2xl font-semibold tracking-tight text-ivory sm:text-3xl">
            Travaillons ensemble
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-titanium sm:text-base">
            Tu es créatrice de contenu, une marque, ou tu veux proposer une
            collaboration ? On lit tout.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-6 rounded-2xl border border-white/10 bg-surface/60 p-5 sm:p-7"
        >
          <div className="space-y-2">
            <label className="text-sm text-ivory/90">Nom *</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="border-white/10 bg-obsidian/50"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-ivory/90">Email *</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="border-white/10 bg-obsidian/50"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-ivory/90">Type de collaboration</label>
            <div className="grid grid-cols-2 gap-2">
              {PUBLIC_REQUEST_TYPES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setType(t.id)}
                  className={cn(
                    "rounded-xl border px-3 py-3 text-left text-sm transition",
                    type === t.id
                      ? "border-copper/50 bg-copper/10 text-ivory"
                      : "border-white/10 bg-obsidian/30 text-titanium hover:border-white/20"
                  )}
                >
                  <span className="mr-1.5">{t.emoji}</span>
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-ivory/90">
              Quel projet ALNUA t&apos;intéresse ?
            </label>
            <div className="flex flex-wrap gap-2">
              {PROJECT_OPTIONS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => toggleProject(p)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs transition",
                    projects.includes(p)
                      ? "border-copper/50 bg-copper/15 text-copper-glow"
                      : "border-white/10 text-titanium hover:border-white/20"
                  )}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm text-ivory/90">Instagram</label>
              <Input
                value={instagram}
                onChange={(e) => setInstagram(e.target.value)}
                placeholder="@..."
                className="border-white/10 bg-obsidian/50"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-ivory/90">TikTok</label>
              <Input
                value={tiktok}
                onChange={(e) => setTiktok(e.target.value)}
                placeholder="@..."
                className="border-white/10 bg-obsidian/50"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-ivory/90">Site web</label>
            <Input
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="https://"
              className="border-white/10 bg-obsidian/50"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-ivory/90">Taille d&apos;audience</label>
            <div className="flex flex-wrap gap-2">
              {AUDIENCE_BUCKETS.map((b) => (
                <button
                  key={b}
                  type="button"
                  onClick={() => setAudience(b)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs transition",
                    audience === b
                      ? "border-copper/50 bg-copper/15 text-copper-glow"
                      : "border-white/10 text-titanium hover:border-white/20"
                  )}
                >
                  {b}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-ivory/90">Ton message</label>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={4}
              placeholder="Décris ta proposition en quelques lignes..."
              className="border-white/10 bg-obsidian/50"
            />
          </div>

          {error ? (
            <p className="text-sm text-red-400">{error}</p>
          ) : null}

          <Button
            type="submit"
            disabled={submitting}
            className="w-full bg-copper text-obsidian hover:bg-copper-glow"
          >
            {submitting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            Envoyer ma proposition →
          </Button>
        </form>
      </div>
    </div>
  );
}

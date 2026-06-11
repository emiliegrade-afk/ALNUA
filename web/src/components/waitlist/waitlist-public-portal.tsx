"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Copy, Loader2, Share2 } from "lucide-react";
import { toast } from "sonner";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import { ConfettiBurst } from "@/components/waitlist/confetti-burst";
import { WAITLIST_SOURCES } from "@/components/waitlist/waitlist.constants";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  fetchWaitlistCount,
  fetchWaitlistInfo,
  joinWaitlist,
  type WaitlistProjectInfo,
} from "@/lib/waitlist-api";
import { cn } from "@/lib/utils";

interface WaitlistPublicPortalProps {
  projectSlug: string;
}

function AnimatedCounter({ value }: { value: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (value === 0) {
      setDisplay(0);
      return;
    }
    const duration = 800;
    const start = performance.now();
    const from = display;
    let frame: number;

    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(from + (value - from) * eased));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- animate toward new target only
  }, [value]);

  return <span className="tabular-nums">{display}</span>;
}

export function WaitlistPublicPortal({ projectSlug }: WaitlistPublicPortalProps) {
  const [info, setInfo] = useState<WaitlistProjectInfo | null>(null);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [source, setSource] = useState<string>("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [success, setSuccess] = useState(false);
  const [position, setPosition] = useState(0);
  const [copied, setCopied] = useState(false);

  const refreshCount = useCallback(async () => {
    try {
      setCount(await fetchWaitlistCount(projectSlug));
    } catch {
      /* ignore polling errors */
    }
  }, [projectSlug]);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchWaitlistInfo(projectSlug), fetchWaitlistCount(projectSlug)])
      .then(([projectInfo, total]) => {
        setInfo(projectInfo);
        setCount(total);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Erreur"))
      .finally(() => setLoading(false));
  }, [projectSlug]);

  useEffect(() => {
    const interval = setInterval(refreshCount, 30_000);
    return () => clearInterval(interval);
  }, [refreshCount]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await joinWaitlist({
        project_slug: projectSlug,
        email: email.trim(),
        first_name: firstName.trim() || undefined,
        source: source || undefined,
        message: message.trim() || undefined,
      });
      setPosition(result.position);
      setCount(result.total);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inscription impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const pageUrl =
    typeof window !== "undefined"
      ? window.location.href
      : `/waitlist/${projectSlug}`;

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(pageUrl);
      setCopied(true);
      toast.success("Lien copié !");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Impossible de copier le lien");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-obsidian">
        <Loader2 className="h-8 w-8 animate-spin text-copper" />
      </div>
    );
  }

  if (error && !info) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-obsidian px-6 text-center">
        <p className="text-red-300">{error}</p>
      </div>
    );
  }

  const projectName = info?.project_name ?? projectSlug;

  return (
    <div className="relative min-h-screen overflow-hidden bg-obsidian text-ivory">
      <div
        className="pointer-events-none absolute inset-0 bg-gradient-to-b from-[#1a1210] via-obsidian to-[#0a0c10]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -top-32 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-copper/10 blur-3xl"
        aria-hidden
      />

      <ConfettiBurst active={success} />

      <div className="relative mx-auto flex min-h-screen max-w-lg flex-col px-5 py-8 sm:px-6">
        <header className="mb-10 flex justify-center">
          <AlnuaLogo variant="symbol" height={36} />
        </header>

        {success ? (
          <div className="flex flex-1 flex-col items-center justify-center text-center animate-fade-in">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-copper/40 bg-copper/15">
              <Check className="h-8 w-8 text-copper-glow" />
            </div>
            <h1 className="text-2xl font-semibold sm:text-3xl">
              Tu es n°{position} sur la liste ! 🎉
            </h1>
            <p className="mt-4 max-w-sm text-titanium">
              On te préviendra en avant-première dès que {projectName} est
              disponible.
            </p>
            <Button
              type="button"
              className="mt-8 gap-2 bg-copper text-obsidian hover:bg-copper-glow"
              onClick={handleShare}
            >
              {copied ? (
                <Copy className="h-4 w-4" />
              ) : (
                <Share2 className="h-4 w-4" />
              )}
              Partager avec tes amis
            </Button>
          </div>
        ) : (
          <>
            <section className="mb-8 text-center animate-fade-in">
              <h1 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
                Sois parmi les premières à découvrir{" "}
                <span className="text-copper-glow">{projectName}</span>
              </h1>
              {info?.description ? (
                <p className="mt-4 text-base text-titanium">{info.description}</p>
              ) : null}
            </section>

            {count > 0 ? (
              <div className="mb-8 rounded-xl border border-copper/20 bg-white/[0.03] px-4 py-3 text-center text-sm text-titanium">
                Rejoins{" "}
                <span className="font-semibold text-copper-glow">
                  <AnimatedCounter value={count} />
                </span>{" "}
                personnes sur la liste d&apos;attente
              </div>
            ) : null}

            <form
              onSubmit={handleSubmit}
              className="space-y-4 rounded-2xl border border-white/10 bg-surface/60 p-5 backdrop-blur-sm sm:p-6"
            >
              <div>
                <label htmlFor="email" className="mb-1.5 block text-xs text-titanium">
                  Email *
                </label>
                <Input
                  id="email"
                  type="email"
                  required
                  placeholder="ton@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="border-white/10 bg-obsidian/50"
                />
              </div>

              <div>
                <label htmlFor="firstName" className="mb-1.5 block text-xs text-titanium">
                  Prénom <span className="text-copper/70">(recommandé)</span>
                </label>
                <Input
                  id="firstName"
                  placeholder="Emilie"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="border-white/10 bg-obsidian/50"
                />
              </div>

              <div>
                <label htmlFor="source" className="mb-1.5 block text-xs text-titanium">
                  Comment tu as découvert ALNUA ?
                </label>
                <Select value={source} onValueChange={setSource}>
                  <SelectTrigger id="source" className="border-white/10 bg-obsidian/50">
                    <SelectValue placeholder="Choisis une option" />
                  </SelectTrigger>
                  <SelectContent>
                    {WAITLIST_SOURCES.map((s) => (
                      <SelectItem key={s.id} value={s.id}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label htmlFor="message" className="mb-1.5 block text-xs text-titanium">
                  Pourquoi tu veux essayer ?
                </label>
                <Textarea
                  id="message"
                  placeholder="Dis-nous ce qui t'attire dans cette app…"
                  rows={3}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="border-white/10 bg-obsidian/50 resize-none"
                />
              </div>

              {error ? (
                <p className="text-sm text-red-300">{error}</p>
              ) : null}

              <Button
                type="submit"
                disabled={submitting}
                className={cn(
                  "w-full gap-2 bg-copper text-obsidian hover:bg-copper-glow",
                  submitting && "opacity-70"
                )}
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Je rejoins la liste →
              </Button>
            </form>
          </>
        )}

        <footer className="mt-auto pt-10 text-center text-xs text-titanium/60">
          © ALNUA 2024
        </footer>
      </div>
    </div>
  );
}

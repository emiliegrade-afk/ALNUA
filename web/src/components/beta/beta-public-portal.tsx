"use client";

import { useCallback, useEffect, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Camera, Loader2, Send } from "lucide-react";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import {
  BETA_FEEDBACK_TYPES,
  BETA_SEVERITIES,
  BETA_TYPE_LABELS,
  severityStyle,
} from "@/components/beta/beta.constants";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  betaProfileKey,
  betaStorageKey,
  fetchBetaInfo,
  fetchMyBetaFeedback,
  registerBetaTester,
  submitBetaFeedback,
  type BetaFeedback,
  type BetaFeedbackType,
  type BetaProjectInfo,
  type BetaSeverity,
  type BetaStoredProfile,
} from "@/lib/beta-api";
import { cn } from "@/lib/utils";

interface BetaPublicPortalProps {
  projectSlug: string;
}

export function BetaPublicPortal({ projectSlug }: BetaPublicPortalProps) {
  const [info, setInfo] = useState<BetaProjectInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [token, setToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<BetaStoredProfile | null>(null);

  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [device, setDevice] = useState("");
  const [osVersion, setOsVersion] = useState("");
  const [appVersion, setAppVersion] = useState("");
  const [registering, setRegistering] = useState(false);

  const [feedbackType, setFeedbackType] = useState<BetaFeedbackType>("bug");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState<BetaSeverity>("mineur");
  const [screenshotPreview, setScreenshotPreview] = useState<string | null>(null);
  const [screenshotBase64, setScreenshotBase64] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [history, setHistory] = useState<BetaFeedback[]>([]);

  const selectedType = BETA_FEEDBACK_TYPES.find((t) => t.id === feedbackType)!;

  useEffect(() => {
    const storedToken = localStorage.getItem(betaStorageKey(projectSlug));
    const storedProfile = localStorage.getItem(betaProfileKey(projectSlug));
    if (storedToken) setToken(storedToken);
    if (storedProfile) {
      try {
        setProfile(JSON.parse(storedProfile) as BetaStoredProfile);
      } catch {
        /* ignore */
      }
    }
  }, [projectSlug]);

  useEffect(() => {
    setLoading(true);
    fetchBetaInfo(projectSlug)
      .then((data) => {
        setInfo(data);
        if (data.app_version) {
          setAppVersion((prev) => prev || data.app_version || "");
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Erreur"))
      .finally(() => setLoading(false));
  }, [projectSlug]);

  const loadHistory = useCallback(async (authToken: string) => {
    try {
      setHistory(await fetchMyBetaFeedback(authToken));
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    if (token) loadHistory(token);
  }, [token, loadHistory]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegistering(true);
    setError(null);
    try {
      const result = await registerBetaTester({
        project_slug: projectSlug,
        email: email.trim(),
        first_name: firstName.trim(),
        device: device.trim() || undefined,
        os_version: osVersion.trim() || undefined,
        app_version: appVersion.trim() || undefined,
      });
      localStorage.setItem(betaStorageKey(projectSlug), result.token);
      const storedProfile: BetaStoredProfile = {
        first_name: result.first_name ?? firstName.trim(),
        project_name: result.project_name,
        app_version: result.app_version,
      };
      localStorage.setItem(betaProfileKey(projectSlug), JSON.stringify(storedProfile));
      setToken(result.token);
      setProfile(storedProfile);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inscription impossible");
    } finally {
      setRegistering(false);
    }
  };

  const handleScreenshot = (file: File | null) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setScreenshotPreview(dataUrl);
      setScreenshotBase64(dataUrl);
    };
    reader.readAsDataURL(file);
  };

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setSeverity("mineur");
    setScreenshotPreview(null);
    setScreenshotBase64(null);
    setSuccess(false);
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitBetaFeedback(token, {
        project_slug: projectSlug,
        type: feedbackType,
        title: title.trim(),
        description: description.trim(),
        severity,
        screenshot_base64: screenshotBase64 ?? undefined,
      });
      setSuccess(true);
      await loadHistory(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Envoi impossible");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-obsidian">
        <Loader2 className="h-8 w-8 animate-spin text-copper" />
      </div>
    );
  }

  if (error && !info) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-obsidian px-4">
        <p className="text-center text-red-300">{error}</p>
      </div>
    );
  }

  const displayName = profile?.first_name ?? firstName;
  const displayVersion = profile?.app_version ?? appVersion ?? info?.app_version ?? "—";

  return (
    <div className="min-h-dvh bg-obsidian text-ivory">
      <div className="pointer-events-none fixed inset-0 bg-radial-glow" />
      <div className="relative mx-auto w-full max-w-[480px] px-4 py-8 pb-16">
        <div className="mb-8 flex flex-col items-center gap-3">
          <AlnuaLogo variant="symbol" height={48} />
          <p className="text-sm text-copper-glow">{info?.project_name}</p>
        </div>

        {!token ? (
          <section className="animate-fade-in space-y-6">
            <div className="text-center">
              <h1 className="text-xl font-semibold text-ivory">
                Programme Beta — {info?.project_name}
              </h1>
              {info?.test_instructions ? (
                <p className="mt-3 text-sm leading-relaxed text-titanium">
                  {info.test_instructions}
                </p>
              ) : null}
            </div>

            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs text-titanium">Prénom</label>
                <Input
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Ton prénom"
                  className="border-copper/15 bg-obsidian/50"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs text-titanium">Email</label>
                <Input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ton@email.com"
                  className="border-copper/15 bg-obsidian/50"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs text-titanium">Appareil</label>
                <Input
                  value={device}
                  onChange={(e) => setDevice(e.target.value)}
                  placeholder="iPhone 14, Samsung S23…"
                  className="border-copper/15 bg-obsidian/50"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-xs text-titanium">Version OS</label>
                  <Input
                    value={osVersion}
                    onChange={(e) => setOsVersion(e.target.value)}
                    placeholder="iOS 17.2"
                    className="border-copper/15 bg-obsidian/50"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs text-titanium">Version app</label>
                  <Input
                    value={appVersion}
                    onChange={(e) => setAppVersion(e.target.value)}
                    placeholder="0.9.1"
                    className="border-copper/15 bg-obsidian/50"
                  />
                </div>
              </div>

              {error ? <p className="text-sm text-red-300">{error}</p> : null}

              <Button
                type="submit"
                disabled={registering}
                className="w-full bg-copper text-obsidian hover:bg-copper-glow"
              >
                {registering ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Rejoindre le programme"
                )}
              </Button>
            </form>
          </section>
        ) : success ? (
          <section className="animate-fade-in space-y-6 text-center">
            <div className="rounded-2xl border border-copper/30 bg-copper/10 p-8">
              <p className="text-lg font-medium text-ivory">
                Merci ! Ton feedback a été transmis à l&apos;équipe 🙌
              </p>
            </div>
            <Button
              onClick={resetForm}
              variant="outline"
              className="w-full border-copper/30 text-copper-glow"
            >
              Envoyer un autre
            </Button>
          </section>
        ) : (
          <section className="animate-fade-in space-y-6">
            <header className="text-center">
              <p className="text-base text-ivory">
                Bonjour {displayName} 👋
              </p>
              <p className="mt-1 text-sm text-titanium">
                Tu testes {info?.project_name} v{displayVersion}
              </p>
            </header>

            <form onSubmit={handleSubmitFeedback} className="space-y-5">
              <div>
                <p className="mb-2 text-xs text-titanium">Type</p>
                <div className="grid grid-cols-2 gap-2">
                  {BETA_FEEDBACK_TYPES.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setFeedbackType(t.id)}
                      className={cn(
                        "flex items-center justify-center gap-2 rounded-xl border px-3 py-3 text-sm transition",
                        feedbackType === t.id
                          ? "border-copper/50 bg-copper/15 text-copper-light"
                          : "border-copper/15 bg-obsidian-deep/50 text-titanium hover:border-copper/30"
                      )}
                    >
                      <span>{t.icon}</span>
                      <span>{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs text-titanium">Titre</label>
                <Input
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder={selectedType.titlePlaceholder}
                  className="border-copper/15 bg-obsidian/50"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs text-titanium">Description</label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={selectedType.descriptionPlaceholder}
                  rows={4}
                  className="border-copper/15 bg-obsidian/50 resize-none"
                />
              </div>

              <div>
                <p className="mb-2 text-xs text-titanium">Sévérité</p>
                <div className="flex flex-wrap gap-2">
                  {BETA_SEVERITIES.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setSeverity(s.id)}
                      className={cn(
                        "rounded-full border px-3 py-1.5 text-xs font-medium transition",
                        severity === s.id
                          ? s.className
                          : "border-copper/15 bg-obsidian-deep/50 text-titanium"
                      )}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="mb-2 text-xs text-titanium">Screenshot (optionnel)</p>
                <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-copper/20 bg-obsidian-deep/40 px-4 py-4 text-sm text-titanium transition hover:border-copper/40">
                  <Camera className="h-4 w-4" />
                  Ajouter une capture
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => handleScreenshot(e.target.files?.[0] ?? null)}
                  />
                </label>
                {screenshotPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={screenshotPreview}
                    alt="Aperçu"
                    className="mt-3 max-h-48 w-full rounded-xl border border-copper/15 object-contain"
                  />
                ) : null}
              </div>

              {error ? <p className="text-sm text-red-300">{error}</p> : null}

              <Button
                type="submit"
                disabled={submitting}
                className="w-full gap-2 bg-copper text-obsidian hover:bg-copper-glow"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Envoyer
                    <Send className="h-4 w-4" />
                  </>
                )}
              </Button>
            </form>
          </section>
        )}

        {token && history.length > 0 ? (
          <section className="mt-12 border-t border-copper/15 pt-8">
            <h2 className="mb-4 text-sm font-medium text-titanium">
              Tes feedbacks précédents
            </h2>
            <ul className="space-y-3">
              {history.map((item) => (
                <li
                  key={item.id}
                  className="rounded-xl border border-copper/15 bg-obsidian-deep/50 p-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium text-ivory">{item.title}</p>
                    <span
                      className={cn(
                        "shrink-0 rounded-full border px-2 py-0.5 text-[10px]",
                        severityStyle(item.severity)
                      )}
                    >
                      {item.severity ?? "—"}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-titanium">
                    {BETA_TYPE_LABELS[item.type ?? "autre"]} ·{" "}
                    {format(new Date(item.created_at), "d MMM yyyy", { locale: fr })}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </div>
  );
}

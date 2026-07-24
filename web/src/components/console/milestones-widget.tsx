"use client";

import { useEffect, useState } from "react";
import { Calendar, CheckCircle2, Circle, Loader2, Pencil, Plus } from "lucide-react";
import { toast } from "sonner";
import {
  createMilestone,
  fetchMilestones,
  updateMilestone,
  validateMilestone,
  type Milestone,
} from "@/lib/milestones-api";
import { Widget } from "./widget";

function daysUntil(dateStr: string): number | null {
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return null;
  const now = new Date();
  return Math.ceil((d.getTime() - now.getTime()) / 86_400_000);
}

interface FormState {
  eventId: string | null;
  title: string;
  dateLocal: string;
  pole: string;
  description: string;
}

const EMPTY_FORM: FormState = { eventId: null, title: "", dateLocal: "", pole: "", description: "" };

export function MilestonesWidget() {
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [notConnected, setNotConnected] = useState(false);
  const [form, setForm] = useState<FormState | null>(null);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const rows = await fetchMilestones();
      setMilestones(rows);
      setNotConnected(false);
    } catch {
      setNotConnected(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function toggleValidated(m: Milestone) {
    const next = !m.validated;
    setMilestones((prev) => prev.map((x) => (x.id === m.id ? { ...x, validated: next } : x)));
    try {
      await validateMilestone(m.id, next);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de la validation");
      setMilestones((prev) => prev.map((x) => (x.id === m.id ? { ...x, validated: !next } : x)));
    }
  }

  function openCreate() {
    setForm({ ...EMPTY_FORM });
  }

  function openEdit(m: Milestone) {
    setForm({
      eventId: m.id,
      title: m.title,
      dateLocal: m.date ? m.date.slice(0, 16) : "",
      pole: m.pole,
      description: m.description,
    });
  }

  async function handleSave() {
    if (!form || !form.title.trim() || !form.dateLocal) return;
    setSaving(true);
    try {
      const iso = new Date(form.dateLocal).toISOString();
      const res = form.eventId
        ? await updateMilestone(form.eventId, {
            title: form.title.trim(),
            date_iso: iso,
            pole: form.pole,
            description: form.description,
          })
        : await createMilestone(form.title.trim(), iso, form.pole, form.description);
      if (!res.success) {
        toast.error(res.error || "Échec de l'enregistrement");
        return;
      }
      toast.success(form.eventId ? "Jalon modifié." : "Jalon créé.");
      setForm(null);
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Widget
      title="Jalons à venir"
      icon={Calendar}
      span="lg:col-span-12"
      delay={0.3}
      bodyClassName="!p-0"
      action={
        <button
          type="button"
          onClick={openCreate}
          aria-label="Ajouter un jalon"
          className="flex items-center gap-1 rounded-lg border border-bronze-faint px-2 py-1 text-[10px] text-titane/70 transition hover:border-bronze/40 hover:text-bronze-bright"
        >
          <Plus className="h-3 w-3" />
          Ajouter
        </button>
      }
    >
      {form ? (
        <div className="space-y-2 border-b border-bronze-faint p-4">
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Titre du jalon"
              className="rounded-lg border border-bronze-faint bg-obsidian px-3 py-1.5 text-sm text-ivoire outline-none placeholder:text-titane/40 focus:border-bronze/50"
            />
            <input
              type="datetime-local"
              value={form.dateLocal}
              onChange={(e) => setForm({ ...form, dateLocal: e.target.value })}
              className="rounded-lg border border-bronze-faint bg-obsidian px-3 py-1.5 text-sm text-ivoire outline-none focus:border-bronze/50"
            />
          </div>
          <input
            value={form.pole}
            onChange={(e) => setForm({ ...form, pole: e.target.value })}
            placeholder="Pôle (ex: R&D, APP, MARKETING…)"
            className="w-full rounded-lg border border-bronze-faint bg-obsidian px-3 py-1.5 text-sm text-ivoire outline-none placeholder:text-titane/40 focus:border-bronze/50"
          />
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Description (optionnelle)"
            rows={2}
            className="w-full resize-none rounded-lg border border-bronze-faint bg-obsidian px-3 py-1.5 text-sm text-ivoire outline-none placeholder:text-titane/40 focus:border-bronze/50"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setForm(null)}
              className="rounded-lg px-3 py-1.5 text-xs text-titane/60 hover:text-ivoire"
            >
              Annuler
            </button>
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={saving || !form.title.trim() || !form.dateLocal}
              aria-label={form.eventId ? "Enregistrer le jalon" : "Créer le jalon"}
              className="flex items-center gap-1.5 rounded-lg bg-bronze px-3 py-1.5 text-xs font-medium text-obsidian hover:bg-bronze-bright disabled:opacity-50"
            >
              {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
              {form.eventId ? "Enregistrer" : "Créer"}
            </button>
          </div>
        </div>
      ) : null}

      {loading ? (
        <p className="flex items-center gap-2 p-4 text-sm text-titane/50">
          <Loader2 className="h-4 w-4 animate-spin" />
          Chargement des jalons…
        </p>
      ) : notConnected ? (
        <p className="p-4 text-xs text-titane/55">
          Google Calendar non connecté — envoie <code className="text-bronze-bright">/connect calendar</code>{" "}
          à Nadia sur Telegram pour activer les jalons réels.
        </p>
      ) : milestones.length === 0 ? (
        <p className="p-4 text-xs text-titane/55">
          Aucun jalon à venir. Clique « Ajouter » pour en créer un — il sera écrit directement dans ton
          Google Calendar (tag <code className="text-bronze-bright">[JALON]</code>).
        </p>
      ) : (
        <div className="grid grid-cols-2 divide-y divide-bronze-faint md:grid-cols-3 md:divide-y-0 md:divide-x lg:grid-cols-6">
          {milestones.map((m) => {
            const days = daysUntil(m.date);
            return (
              <div key={m.id} className="group relative p-4">
                <div className="mb-2 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => void toggleValidated(m)}
                    aria-label={m.validated ? "Marquer comme non validé" : "Valider ce jalon"}
                    title={m.validated ? "Validé" : "Valider"}
                    className="shrink-0"
                  >
                    {m.validated ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <Circle className="h-5 w-5 text-titane/40 hover:text-bronze-bright" />
                    )}
                  </button>
                  <span className="text-[9px] uppercase tracking-wide text-titane/50">
                    {m.pole || "—"}
                  </span>
                  <button
                    type="button"
                    onClick={() => openEdit(m)}
                    aria-label="Modifier ce jalon"
                    className="ml-auto text-titane/30 opacity-0 transition group-hover:opacity-100 hover:text-bronze-bright"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                </div>
                <p className="mb-1 text-xs font-medium leading-snug text-ivoire">{m.title}</p>
                <p className="text-[10px] text-titane/50">
                  {days === null ? m.date : days <= 0 ? "aujourd'hui" : `dans ${days} j`}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </Widget>
  );
}

"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  createCampaign,
  updateCampaign,
  type Campaign,
  type CampaignInput,
  type CampaignObjective,
  type CampaignPlatform,
  type CampaignStatus,
} from "@/lib/marketing-api";
import type { Project } from "@/lib/types";

/* Modale de création/édition manuelle de campagne — calquée étroitement sur
   finances-transaction-modal.tsx (mêmes primitives, même structure). Phase
   33, ROADMAP.md. */

const OBJECTIVES: { value: CampaignObjective; label: string }[] = [
  { value: "awareness", label: "Notoriété" },
  { value: "traffic", label: "Trafic" },
  { value: "conversions", label: "Conversions" },
  { value: "engagement", label: "Engagement" },
  { value: "video_views", label: "Vues vidéo" },
];

const PLATFORMS: { value: CampaignPlatform; label: string }[] = [
  { value: "meta", label: "Meta (Facebook/Instagram)" },
  { value: "google", label: "Google Ads" },
  { value: "tiktok", label: "TikTok" },
];

const STATUSES: { value: CampaignStatus; label: string }[] = [
  { value: "draft", label: "Brouillon" },
  { value: "active", label: "En cours" },
  { value: "paused", label: "En pause" },
  { value: "completed", label: "Terminée" },
];

interface CampaignModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  campaign?: Campaign | null;
  onSaved: (campaign: Campaign) => void;
}

export function CampaignModal({
  open,
  onOpenChange,
  projects,
  campaign,
  onSaved,
}: CampaignModalProps) {
  const isEdit = Boolean(campaign);

  const [name, setName] = useState("");
  const [objective, setObjective] = useState<CampaignObjective>("awareness");
  const [platform, setPlatform] = useState<CampaignPlatform>("meta");
  const [status, setStatus] = useState<CampaignStatus>("draft");
  const [budget, setBudget] = useState("");
  const [projectId, setProjectId] = useState<string>("none");
  const [audience, setAudience] = useState("");
  const [brief, setBrief] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reach, setReach] = useState("");
  const [engagements, setEngagements] = useState("");
  const [conversions, setConversions] = useState("");
  const [revenue, setRevenue] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    if (campaign) {
      setName(campaign.name);
      setObjective(campaign.objective);
      setPlatform(campaign.platform);
      setStatus(campaign.status);
      setBudget(String(campaign.budget_allocated_usd));
      setProjectId(campaign.project_id ?? "none");
      setAudience(campaign.audience ?? "");
      setBrief(campaign.brief ?? "");
      setStartDate(campaign.start_date ?? "");
      setEndDate(campaign.end_date ?? "");
      setReach(campaign.reach != null ? String(campaign.reach) : "");
      setEngagements(campaign.engagements != null ? String(campaign.engagements) : "");
      setConversions(campaign.conversions != null ? String(campaign.conversions) : "");
      setRevenue(campaign.revenue_generated_usd != null ? String(campaign.revenue_generated_usd) : "");
    } else {
      setName("");
      setObjective("awareness");
      setPlatform("meta");
      setStatus("draft");
      setBudget("");
      setProjectId("none");
      setAudience("");
      setBrief("");
      setStartDate("");
      setEndDate("");
      setReach("");
      setEngagements("");
      setConversions("");
      setRevenue("");
    }
  }, [open, campaign]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Le nom est requis");
      return;
    }
    const num = parseFloat(budget.replace(",", "."));
    if (Number.isNaN(num) || num < 0) {
      toast.error("Budget invalide");
      return;
    }

    const payload: CampaignInput & {
      reach?: number;
      engagements?: number;
      conversions?: number;
      revenue_generated_usd?: number;
    } = {
      name: name.trim(),
      objective,
      platform,
      status,
      budget_allocated_usd: num,
      project_id: projectId === "none" ? null : projectId,
      audience: audience.trim() || null,
      brief: brief.trim() || null,
      start_date: startDate || null,
      end_date: endDate || null,
    };
    if (reach.trim()) payload.reach = Math.max(0, parseInt(reach, 10) || 0);
    if (engagements.trim()) payload.engagements = Math.max(0, parseInt(engagements, 10) || 0);
    if (conversions.trim()) payload.conversions = Math.max(0, parseInt(conversions, 10) || 0);
    if (revenue.trim()) payload.revenue_generated_usd = Math.max(0, parseFloat(revenue.replace(",", ".")) || 0);

    setSubmitting(true);
    try {
      const saved = campaign
        ? await updateCampaign(campaign.id, payload)
        : await createCampaign(payload);
      toast.success(campaign ? "Campagne mise à jour" : "Campagne créée");
      onSaved(saved);
      onOpenChange(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto border-copper/15 bg-surface sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-ivory">
            {isEdit ? "Modifier la campagne" : "Nouvelle campagne"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="campaign-name">Nom *</Label>
            <Input
              id="campaign-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex. Lancement NUAWAY — vanlifers EU"
              className="border-copper/15 bg-obsidian-deep/50"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Plateforme</Label>
              <Select value={platform} onValueChange={(v) => setPlatform(v as CampaignPlatform)}>
                <SelectTrigger className="border-copper/15 bg-obsidian-deep/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PLATFORMS.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Objectif</Label>
              <Select value={objective} onValueChange={(v) => setObjective(v as CampaignObjective)}>
                <SelectTrigger className="border-copper/15 bg-obsidian-deep/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {OBJECTIVES.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="campaign-budget">Budget alloué ($)</Label>
              <Input
                id="campaign-budget"
                type="text"
                inputMode="decimal"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="500"
                className="border-copper/15 bg-obsidian-deep/50"
              />
            </div>
            <div className="space-y-2">
              <Label>Statut</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as CampaignStatus)}>
                <SelectTrigger className="border-copper/15 bg-obsidian-deep/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Projet (optionnel)</Label>
            <Select value={projectId} onValueChange={setProjectId}>
              <SelectTrigger className="border-copper/15 bg-obsidian-deep/50">
                <SelectValue placeholder="ALNUA global" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">ALNUA global</SelectItem>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="campaign-start">Début</Label>
              <Input
                id="campaign-start"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="border-copper/15 bg-obsidian-deep/50"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="campaign-end">Fin</Label>
              <Input
                id="campaign-end"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="border-copper/15 bg-obsidian-deep/50"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="campaign-audience">Audience (optionnel)</Label>
            <Input
              id="campaign-audience"
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              placeholder="Lookalike, retargeting…"
              className="border-copper/15 bg-obsidian-deep/50"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="campaign-brief">Brief (optionnel)</Label>
            <Textarea
              id="campaign-brief"
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="Contexte, message clé…"
              rows={2}
              className="border-copper/15 bg-obsidian-deep/50"
            />
          </div>

          {isEdit && (
            <div className="space-y-2 rounded-lg border border-copper/15 bg-obsidian-deep/40 p-3">
              <Label className="text-[11px] uppercase tracking-wide text-muted-foreground">
                Statistiques (saisie manuelle depuis le dashboard de la plateforme)
              </Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="campaign-reach" className="text-xs">Reach</Label>
                  <Input
                    id="campaign-reach"
                    type="text"
                    inputMode="numeric"
                    value={reach}
                    onChange={(e) => setReach(e.target.value)}
                    placeholder="Non renseigné"
                    className="border-copper/15 bg-obsidian-deep/50"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="campaign-engagements" className="text-xs">Engagements</Label>
                  <Input
                    id="campaign-engagements"
                    type="text"
                    inputMode="numeric"
                    value={engagements}
                    onChange={(e) => setEngagements(e.target.value)}
                    placeholder="Non renseigné"
                    className="border-copper/15 bg-obsidian-deep/50"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="campaign-conversions" className="text-xs">Conversions</Label>
                  <Input
                    id="campaign-conversions"
                    type="text"
                    inputMode="numeric"
                    value={conversions}
                    onChange={(e) => setConversions(e.target.value)}
                    placeholder="Non renseigné"
                    className="border-copper/15 bg-obsidian-deep/50"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="campaign-revenue" className="text-xs">Revenu généré ($)</Label>
                  <Input
                    id="campaign-revenue"
                    type="text"
                    inputMode="decimal"
                    value={revenue}
                    onChange={(e) => setRevenue(e.target.value)}
                    placeholder="Non renseigné"
                    className="border-copper/15 bg-obsidian-deep/50"
                  />
                </div>
              </div>
              {campaign?.stats_updated_at && (
                <p className="text-[10px] text-muted-foreground">
                  Dernière mise à jour : {new Date(campaign.stats_updated_at).toLocaleString("fr-FR")}
                </p>
              )}
              {campaign?.spent_usd != null && campaign.spent_usd > 0 && (
                <p className="text-[10px] text-muted-foreground">
                  ROI calculé automatiquement si un revenu est renseigné (dépensé réel : {campaign.spent_usd} $).
                </p>
              )}
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Enregistrement…" : "Enregistrer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Copy,
  ExternalLink,
  FileText,
  FolderOpen,
  Link2,
  Loader2,
  MessageSquarePlus,
} from "lucide-react";
import { toast } from "sonner";
import { AffiliateChart } from "@/components/partnerships/affiliate-chart";
import {
  INTERACTION_TYPES,
  PARTNER_STATUSES,
  PARTNER_TYPES,
  partnerStatusLabel,
  partnerTypeLabel,
} from "@/components/partnerships/partnerships.constants";
import { Badge } from "@/components/ui/badge";
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
  affiliateGoUrl,
  createAffiliateLink,
  createPartnerInteraction,
  fetchAffiliateLinks,
  fetchPartnerInteractions,
  openContractsFolder,
  openPartnerContract,
  updatePartner,
  uploadPartnerContract,
  type AffiliateLink,
  type Partner,
  type PartnerInteraction,
} from "@/lib/partnerships-api";
import type { Project } from "@/lib/types";

interface PartnerDetailPanelProps {
  partner: Partner;
  projects: Project[];
  onUpdate: (partner: Partner) => void;
}

export function PartnerDetailPanel({
  partner,
  projects,
  onUpdate,
}: PartnerDetailPanelProps) {
  const [interactions, setInteractions] = useState<PartnerInteraction[]>([]);
  const [affiliateLinks, setAffiliateLinks] = useState<AffiliateLink[]>([]);
  const [loadingIx, setLoadingIx] = useState(true);
  const [showIxForm, setShowIxForm] = useState(false);
  const [ixType, setIxType] = useState("email");
  const [ixNote, setIxNote] = useState("");
  const [notes, setNotes] = useState(partner.notes ?? "");
  const [followup, setFollowup] = useState(partner.next_followup ?? "");
  const [uploading, setUploading] = useState(false);
  const [newLinkUrl, setNewLinkUrl] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const notesTimer = useRef<ReturnType<typeof setTimeout>>();

  const loadInteractions = useCallback(async () => {
    setLoadingIx(true);
    try {
      setInteractions(await fetchPartnerInteractions(partner.id));
    } catch {
      setInteractions([]);
    } finally {
      setLoadingIx(false);
    }
  }, [partner.id]);

  const loadAffiliateLinks = useCallback(async () => {
    if (partner.type !== "affiliate") return;
    try {
      setAffiliateLinks(await fetchAffiliateLinks(partner.id));
    } catch {
      setAffiliateLinks([]);
    }
  }, [partner.id, partner.type]);

  useEffect(() => {
    loadInteractions();
    loadAffiliateLinks();
  }, [loadInteractions, loadAffiliateLinks]);

  useEffect(() => {
    setNotes(partner.notes ?? "");
    setFollowup(partner.next_followup ?? "");
  }, [partner.id, partner.notes, partner.next_followup]);

  const patch = async (fields: Partial<Partner>) => {
    const updated = await updatePartner(partner.id, fields);
    onUpdate(updated);
  };

  const saveNotes = (value: string) => {
    setNotes(value);
    clearTimeout(notesTimer.current);
    notesTimer.current = setTimeout(() => {
      patch({ notes: value }).catch(() => toast.error("Sauvegarde impossible"));
    }, 600);
  };

  const addInteraction = async () => {
    try {
      await createPartnerInteraction(partner.id, {
        type: ixType,
        note: ixNote,
      });
      setIxNote("");
      setShowIxForm(false);
      loadInteractions();
      toast.success("Interaction ajoutée");
    } catch {
      toast.error("Erreur");
    }
  };

  const handleContractUpload = async (file: File) => {
    setUploading(true);
    try {
      const updated = await uploadPartnerContract(partner.id, file);
      onUpdate(updated);
      toast.success("Contrat enregistré");
    } catch {
      toast.error("Upload impossible");
    } finally {
      setUploading(false);
    }
  };

  const createLink = async () => {
    if (!newLinkUrl.trim()) return;
    try {
      await createAffiliateLink({
        partner_id: partner.id,
        redirect_url: newLinkUrl.trim(),
        project_id: partner.project_ids[0],
      });
      setNewLinkUrl("");
      loadAffiliateLinks();
      toast.success("Lien créé");
    } catch {
      toast.error("Création impossible");
    }
  };

  const copyLink = (code: string) => {
    void navigator.clipboard.writeText(affiliateGoUrl(code));
    toast.success("Lien copié");
  };

  const projectMap = Object.fromEntries(projects.map((p) => [p.id, p]));

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="shrink-0 border-b border-white/10 p-4">
        <Input
          value={partner.name}
          onChange={(e) => onUpdate({ ...partner, name: e.target.value })}
          onBlur={(e) => patch({ name: e.target.value })}
          className="border-transparent bg-transparent text-lg font-semibold text-ivory focus:border-white/20"
        />
        <div className="mt-2 flex flex-wrap gap-2">
          <Select
            value={partner.type}
            onValueChange={(v) => patch({ type: v }).catch(() => {})}
          >
            <SelectTrigger className="h-8 w-auto border-white/10 text-xs">
              <SelectValue>{partnerTypeLabel(partner.type)}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {PARTNER_TYPES.map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={partner.status}
            onValueChange={(v) => patch({ status: v }).catch(() => {})}
          >
            <SelectTrigger className="h-8 w-auto border-white/10 text-xs">
              <SelectValue>{partnerStatusLabel(partner.status)}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {PARTNER_STATUSES.map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {partner.instagram_url ? (
            <a
              href={partner.instagram_url}
              target="_blank"
              rel="noreferrer"
              className="text-copper-glow hover:underline"
            >
              Instagram <ExternalLink className="inline h-3 w-3" />
            </a>
          ) : null}
          {partner.tiktok_url ? (
            <a
              href={partner.tiktok_url}
              target="_blank"
              rel="noreferrer"
              className="text-copper-glow hover:underline"
            >
              TikTok <ExternalLink className="inline h-3 w-3" />
            </a>
          ) : null}
          {partner.website ? (
            <a
              href={partner.website}
              target="_blank"
              rel="noreferrer"
              className="text-copper-glow hover:underline"
            >
              Site <ExternalLink className="inline h-3 w-3" />
            </a>
          ) : null}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            className="border-white/10 text-xs"
            onClick={() => setShowIxForm(true)}
          >
            <MessageSquarePlus className="mr-1 h-3 w-3" />
            Interaction
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-white/10 text-xs"
            onClick={() => fileRef.current?.click()}
          >
            <FileText className="mr-1 h-3 w-3" />
            Contrat
          </Button>
        </div>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto p-4">
        <section>
          <h3 className="text-xs font-medium uppercase tracking-wide text-titanium">
            Profil
          </h3>
          <div className="mt-2 space-y-2 text-sm text-ivory/90">
            {partner.audience_description ? (
              <p>{partner.audience_description}</p>
            ) : null}
            {partner.audience_size ? (
              <p className="text-titanium">
                Audience : ~{partner.audience_size.toLocaleString("fr-FR")} abonnés
              </p>
            ) : null}
            {partner.project_ids.length > 0 ? (
              <div className="flex flex-wrap gap-1">
                {partner.project_ids.map((id) => (
                  <Badge key={id} variant="outline" className="text-[10px]">
                    {projectMap[id]?.name ?? id}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
          <Textarea
            value={notes}
            onChange={(e) => saveNotes(e.target.value)}
            placeholder="Notes internes..."
            rows={4}
            className="mt-3 border-white/10 bg-obsidian/40 text-sm"
          />
          <div className="mt-3 flex items-center gap-2">
            <Input
              type="date"
              value={followup}
              onChange={(e) => setFollowup(e.target.value)}
              className="border-white/10 bg-obsidian/40 text-sm"
            />
            <Button
              size="sm"
              variant="outline"
              className="border-white/10 shrink-0"
              onClick={() =>
                patch({ next_followup: followup || null }).then(() =>
                  toast.success("Relance enregistrée")
                )
              }
            >
              Définir relance
            </Button>
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-medium uppercase tracking-wide text-titanium">
              Historique
            </h3>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={() => setShowIxForm(true)}
            >
              + Ajouter
            </Button>
          </div>
          {showIxForm ? (
            <div className="mt-2 space-y-2 rounded-lg border border-white/10 p-3">
              <Select value={ixType} onValueChange={setIxType}>
                <SelectTrigger className="border-white/10 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {INTERACTION_TYPES.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.icon} {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Textarea
                value={ixNote}
                onChange={(e) => setIxNote(e.target.value)}
                placeholder="Note..."
                rows={2}
                className="border-white/10 text-sm"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={addInteraction}>
                  Enregistrer
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowIxForm(false)}
                >
                  Annuler
                </Button>
              </div>
            </div>
          ) : null}
          {loadingIx ? (
            <Loader2 className="mt-4 h-5 w-5 animate-spin text-titanium" />
          ) : (
            <ul className="mt-3 space-y-3 border-l border-white/10 pl-4">
              {interactions.map((ix) => {
                const meta = INTERACTION_TYPES.find((t) => t.id === ix.type);
                return (
                  <li key={ix.id} className="relative">
                    <span className="absolute -left-[1.35rem] top-1 h-2 w-2 rounded-full bg-copper" />
                    <p className="text-[11px] text-titanium">
                      {format(parseISO(ix.date), "d MMM yyyy · HH:mm", {
                        locale: fr,
                      })}
                    </p>
                    <p className="text-sm text-ivory">
                      {meta?.icon} {meta?.label ?? ix.type}
                    </p>
                    {ix.note ? (
                      <p className="mt-0.5 text-sm text-titanium">{ix.note}</p>
                    ) : null}
                  </li>
                );
              })}
              {!interactions.length ? (
                <li className="text-sm text-titanium">Aucune interaction</li>
              ) : null}
            </ul>
          )}
        </section>

        <section>
          <h3 className="text-xs font-medium uppercase tracking-wide text-titanium">
            Contrat
          </h3>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void handleContractUpload(f);
            }}
          />
          {partner.contract_path ? (
            <div className="mt-2 space-y-2">
              <p className="truncate text-xs text-titanium">
                {partner.contract_path}
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="border-white/10"
                  onClick={() =>
                    openPartnerContract(partner.id).catch(() =>
                      toast.error("Impossible d'ouvrir le PDF")
                    )
                  }
                >
                  Ouvrir le PDF
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-white/10"
                  onClick={() => fileRef.current?.click()}
                  disabled={uploading}
                >
                  Remplacer
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-2 space-y-2">
              <Button
                size="sm"
                variant="outline"
                className="border-white/10"
                onClick={() => fileRef.current?.click()}
                disabled={uploading}
              >
                {uploading ? (
                  <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="mr-1 h-4 w-4" />
                )}
                Upload PDF
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-titanium"
                onClick={() =>
                  openContractsFolder().catch(() =>
                    toast.error("Dossier inaccessible")
                  )
                }
              >
                <FolderOpen className="mr-1 h-4 w-4" />
                Ouvrir dossier contrats
              </Button>
            </div>
          )}
        </section>

        {partner.type === "affiliate" ? (
          <section>
            <h3 className="text-xs font-medium uppercase tracking-wide text-titanium">
              Lien affilié
            </h3>
            {affiliateLinks.map((link) => (
              <div
                key={link.id}
                className="mt-2 rounded-lg border border-white/10 p-3"
              >
                <div className="flex items-center justify-between">
                  <code className="text-sm text-copper-glow">{link.code}</code>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyLink(link.code)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <p className="mt-1 truncate text-xs text-titanium">
                  → {link.redirect_url}
                </p>
                <div className="mt-2 flex gap-4 text-xs text-ivory/80">
                  <span>{link.clicks} clics</span>
                  <span>{link.conversions} conv.</span>
                  <span>
                    {Number(link.revenue_generated).toFixed(2)} €
                  </span>
                </div>
                <div className="mt-3">
                  <AffiliateChart linkId={link.id} />
                </div>
              </div>
            ))}
            <div className="mt-3 flex gap-2">
              <Input
                value={newLinkUrl}
                onChange={(e) => setNewLinkUrl(e.target.value)}
                placeholder="URL de redirection"
                className="border-white/10 text-sm"
              />
              <Button size="sm" onClick={createLink}>
                <Link2 className="h-4 w-4" />
              </Button>
            </div>
          </section>
        ) : null}
      </div>
    </div>
  );
}

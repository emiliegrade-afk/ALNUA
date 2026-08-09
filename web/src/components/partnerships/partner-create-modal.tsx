"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
  PARTNER_TYPES,
} from "@/components/partnerships/partnerships.constants";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createPartner, type Partner } from "@/lib/partnerships-api";
import type { Project } from "@/lib/types";

interface PartnerCreateModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  initial?: Partial<Partner>;
  onCreated: (partner: Partner) => void;
}

export function PartnerCreateModal({
  open,
  onOpenChange,
  projects,
  initial,
  onCreated,
}: PartnerCreateModalProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [type, setType] = useState(initial?.type ?? "influencer");
  const [email, setEmail] = useState(initial?.email ?? "");
  const [direction, setDirection] = useState<"outbound" | "inbound">(
    initial?.direction ?? "outbound"
  );
  const [projectIds, setProjectIds] = useState<string[]>(
    initial?.project_ids ?? []
  );
  const [submitting, setSubmitting] = useState(false);

  const toggleProject = (id: string) => {
    setProjectIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      const partner = await createPartner({
        name: name.trim(),
        type,
        direction,
        email: email.trim() || null,
        project_ids: projectIds,
        notes: initial?.notes ?? "",
        instagram_url: initial?.instagram_url,
        tiktok_url: initial?.tiktok_url,
        website: initial?.website,
        audience_size: initial?.audience_size,
        audience_description: initial?.audience_description,
        status: "prospect",
      });
      onCreated(partner);
      onOpenChange(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-copper/15 bg-surface sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-ivory">Nouveau partenaire</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Nom *"
            required
            className="border-copper/15 bg-obsidian/50"
          />
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="border-copper/15 bg-obsidian/50"
          />
          <Select value={type} onValueChange={setType}>
            <SelectTrigger className="border-copper/15 bg-obsidian/50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PARTNER_TYPES.map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  {t.emoji} {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={direction}
            onValueChange={(v) => setDirection(v as "outbound" | "inbound")}
          >
            <SelectTrigger className="border-copper/15 bg-obsidian/50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="outbound">→ Sortant (on les approche)</SelectItem>
              <SelectItem value="inbound">← Entrant (ils nous contactent)</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex flex-wrap gap-2">
            {projects.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => toggleProject(p.id)}
                className={`rounded-full border px-2 py-0.5 text-xs ${
                  projectIds.includes(p.id)
                    ? "border-copper/50 bg-copper/15 text-copper-glow"
                    : "border-copper/15 text-titanium"
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
          <Button
            type="submit"
            disabled={submitting}
            className="w-full bg-copper text-obsidian"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Créer"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

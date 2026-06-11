"use client";

import { useCallback, useEffect, useState } from "react";
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  REQUEST_STATUSES,
  statusBadgeStyle,
} from "@/components/partnerships/partnerships.constants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  convertPartnershipRequest,
  fetchPartnershipRequests,
  updatePartnershipRequest,
  type PartnershipRequest,
  type Partner,
} from "@/lib/partnerships-api";

interface RequestsTabProps {
  onConverted: (partner: Partner) => void;
}

export function RequestsTab({ onConverted }: RequestsTabProps) {
  const [requests, setRequests] = useState<PartnershipRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<PartnershipRequest | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setRequests(await fetchPartnershipRequests());
    } catch {
      setRequests([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const decline = async (id: string) => {
    try {
      await updatePartnershipRequest(id, { status: "declined" });
      load();
      toast.success("Demande déclinée");
    } catch {
      toast.error("Erreur");
    }
  };

  const convert = async (id: string) => {
    try {
      const result = await convertPartnershipRequest(id);
      onConverted(result.partner);
      load();
      setDrawerOpen(false);
      toast.success("Partenaire créé");
    } catch {
      toast.error("Conversion impossible");
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-titanium" />
      </div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-white/10 text-xs text-titanium">
              <th className="pb-2 pr-3">Nom</th>
              <th className="pb-2 pr-3">Email</th>
              <th className="pb-2 pr-3">Type</th>
              <th className="pb-2 pr-3">Projet</th>
              <th className="pb-2 pr-3">Audience</th>
              <th className="pb-2 pr-3">Date</th>
              <th className="pb-2 pr-3">Statut</th>
              <th className="pb-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id} className="border-b border-white/5">
                <td className="py-2 pr-3 text-ivory">{r.name}</td>
                <td className="py-2 pr-3 text-titanium">{r.email}</td>
                <td className="py-2 pr-3 text-titanium">{r.type ?? "—"}</td>
                <td className="py-2 pr-3 text-titanium">
                  {r.project_interest ?? "—"}
                </td>
                <td className="py-2 pr-3 text-titanium">
                  {r.audience_size ?? "—"}
                </td>
                <td className="py-2 pr-3 text-titanium">
                  {format(parseISO(r.created_at), "d MMM yyyy", { locale: fr })}
                </td>
                <td className="py-2 pr-3">
                  <Badge
                    variant="outline"
                    className={statusBadgeStyle(r.status)}
                  >
                    {REQUEST_STATUSES.find((s) => s.id === r.status)?.label ??
                      r.status}
                  </Badge>
                </td>
                <td className="py-2">
                  <div className="flex flex-wrap gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-xs"
                      onClick={() => {
                        setSelected(r);
                        setDrawerOpen(true);
                      }}
                    >
                      Message
                    </Button>
                    {r.status === "new" || r.status === "reviewed" ? (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 border-emerald-500/30 text-xs text-emerald-300"
                          onClick={() => convert(r.id)}
                        >
                          Convertir
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs text-titanium"
                          onClick={() => decline(r.id)}
                        >
                          Décliner
                        </Button>
                      </>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!requests.length ? (
          <p className="py-8 text-center text-sm text-titanium">
            Aucune demande entrante.
          </p>
        ) : null}
      </div>

      <Dialog open={drawerOpen} onOpenChange={setDrawerOpen}>
        <DialogContent className="border-white/10 bg-surface sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-ivory">
              {selected?.name}
            </DialogTitle>
          </DialogHeader>
          {selected ? (
            <div className="space-y-3 text-sm">
              <p className="text-titanium">{selected.email}</p>
              <p className="whitespace-pre-wrap text-ivory/90">
                {selected.message || "—"}
              </p>
              {selected.instagram_url ? (
                <p className="text-titanium">IG: {selected.instagram_url}</p>
              ) : null}
              {selected.tiktok_url ? (
                <p className="text-titanium">TikTok: {selected.tiktok_url}</p>
              ) : null}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
}

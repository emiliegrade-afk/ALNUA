"use client";

import { useEffect, useState } from "react";
import { Presentation } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RndDossierList } from "@/components/rnd/rnd-dossier-list";
import { RndDossierWorkspace } from "@/components/rnd/rnd-dossier-workspace";
import { RndPitchModal } from "@/components/rnd/rnd-pitch-modal";
import type { RndDossierListItem } from "@/lib/rnd-dossier";

interface RndDossiersViewProps {
  initialDossierId?: string | null;
  initialPitchView?: string;
  reloadKey?: number;
}

export function RndDossiersView({
  initialDossierId,
  initialPitchView,
  reloadKey = 0,
}: RndDossiersViewProps) {
  const [selected, setSelected] = useState<RndDossierListItem | null>(null);
  const [pitchDossierId, setPitchDossierId] = useState<string | null>(null);
  const [pitchOpen, setPitchOpen] = useState(false);
  const [listReloadKey, setListReloadKey] = useState(reloadKey);

  useEffect(() => {
    setListReloadKey(reloadKey);
  }, [reloadKey]);

  useEffect(() => {
    if (initialDossierId) {
      setPitchDossierId(initialDossierId);
      setPitchOpen(true);
    }
  }, [initialDossierId, reloadKey]);

  function handleSelect(d: RndDossierListItem) {
    setSelected(d);
  }

  function openPitch(dossierId: string) {
    setPitchDossierId(dossierId);
    setPitchOpen(true);
  }

  return (
    <>
      <div className="grid h-full min-h-0 gap-4 lg:grid-cols-[minmax(280px,340px)_1fr]">
        <div className="min-h-0 overflow-hidden rounded-xl border border-copper/10 bg-obsidian-2/30 p-4">
          <p className="label-caps mb-3 text-titanium/50">
            Dossiers R&D — sélectionne pour le workspace
          </p>
          <RndDossierList
            selectedId={selected?.id ?? null}
            onSelect={handleSelect}
            reloadKey={listReloadKey}
          />
        </div>

        <div className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-copper/10 bg-obsidian-2/20 p-4">
          {selected ? (
            <div className="mb-3 flex shrink-0 justify-end">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="border-copper/35 text-copper hover:bg-copper/10"
                onClick={() => openPitch(selected.id)}
              >
                <Presentation className="mr-2 h-3.5 w-3.5" />
                Pitch complet
              </Button>
            </div>
          ) : null}
          <div className="min-h-0 flex-1 overflow-hidden">
            <RndDossierWorkspace
              dossierItem={selected}
              onClose={selected ? () => setSelected(null) : undefined}
            />
          </div>
        </div>
      </div>

      <RndPitchModal
        dossierId={pitchDossierId}
        initialViewMode={initialPitchView}
        open={pitchOpen}
        onOpenChange={(open) => {
          setPitchOpen(open);
          if (!open) setPitchDossierId(null);
        }}
        onRefresh={() => setListReloadKey((k) => k + 1)}
      />
    </>
  );
}

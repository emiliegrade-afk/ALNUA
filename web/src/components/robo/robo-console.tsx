"use client";

import { useCallback, useEffect, useState } from "react";
import { AgentActionConsole } from "@/components/shared/agent-action-console";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EveBomPanel } from "@/components/robo/eve-bom-panel";
import {
  embeddedInstruction,
  embeddedPiCommand,
  fetchBomItems,
  fetchEveStatus,
  fetchLookingGlassStatus,
  fetchPiBridgeStatus,
  hardwareInstruction,
  mechanicalBomContext,
  qaRobotLabContext,
  safetyLabContext,
  visionAiPiProbe,
  type BomItem,
} from "@/lib/pole-api";
import { cn } from "@/lib/utils";

export function RoboConsole() {
  const [items, setItems] = useState<BomItem[]>([]);
  const [totals, setTotals] = useState({ total_eur: 0, count: 0, by_category: {} as Record<string, number> });
  const [loading, setLoading] = useState(true);
  const [eveStatus, setEveStatus] = useState({ connected: false, battery: null as number | null });
  const [piBridge, setPiBridge] = useState<{ configured: boolean; message: string }>({
    configured: false,
    message: "",
  });
  const [lgStatus, setLgStatus] = useState({
    connected: false,
    holoplay_running: false,
    message: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    const [bom, eve, lg, bridge] = await Promise.all([
      fetchBomItems().catch(() => ({ items: [], totals: { total_eur: 0, count: 0, by_category: {} } })),
      fetchEveStatus(),
      fetchLookingGlassStatus().catch(() => ({
        connected: false,
        holoplay_running: false,
        message: "Indisponible",
      })),
      fetchPiBridgeStatus().catch(() => ({
        configured: false,
        host: null,
        message: "Statut Pi indisponible",
        tooling: { agents: "", human_files: "" },
      })),
    ]);
    setItems(bom.items);
    setTotals({
      total_eur: bom.totals.total_eur,
      count: bom.totals.count,
      by_category: bom.totals.by_category || {},
    });
    setEveStatus({ connected: eve.connected, battery: eve.battery ?? null });
    setLgStatus(lg);
    setPiBridge({ configured: bridge.configured, message: bridge.message });
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
    const interval = setInterval(load, 60_000);
    return () => clearInterval(interval);
  }, [load]);

  if (loading && items.length === 0) {
    return <p className="text-sm text-titanium/50">Chargement console robotique…</p>;
  }

  return (
    <section className="space-y-6">
      <div className="rounded-lg border border-copper/20 bg-obsidian-2/60 px-3 py-2 text-[11px] text-titanium/70">
        <strong className="text-ivory">Rôles :</strong> robot physique = Yuki / Marco / Ravi / Petra / Zara.
        App compagnon Eve (comme Naïa) = Théo (dev_app) — pas le même job.{" "}
        <strong className="text-ivory">Pi :</strong> {piBridge.message} — brancher plus tard OK ; WinSCP reste
        optionnel pour copier des fichiers à la main.
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="font-title text-base text-ivory">Eve Pi</CardTitle>
          </CardHeader>
          <CardContent>
            <span
              className={cn(
                "inline-flex items-center gap-2 text-sm",
                eveStatus.connected || piBridge.configured ? "text-copper-light" : "text-red-400",
              )}
            >
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  eveStatus.connected ? "bg-copper-light" : piBridge.configured ? "bg-amber-400" : "bg-red-500",
                )}
              />
              {eveStatus.connected
                ? "Online"
                : piBridge.configured
                  ? "SSH configuré (pas encore online)"
                  : "Pas encore branché"}
              {eveStatus.battery != null ? ` · ${eveStatus.battery}%` : ""}
            </span>
          </CardContent>
        </Card>
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="font-title text-base text-ivory">Looking Glass</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <span className={lgStatus.connected ? "badge-copper px-2 py-0.5 text-xs" : "badge-titanium px-2 py-0.5 text-xs"}>
              {lgStatus.connected
                ? lgStatus.holoplay_running
                  ? "HoloPlay actif"
                  : "Host OK"
                : "Non connecté"}
            </span>
            <p className="text-xs text-titanium/60">{lgStatus.message}</p>
          </CardContent>
        </Card>
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="font-title text-base text-ivory">BOM Total</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-title text-lg text-ivory">{totals.total_eur.toFixed(2)} €</p>
            <p className="text-xs text-titanium/60">{totals.count} composants</p>
          </CardContent>
        </Card>
      </div>

      <EveBomPanel items={items} totals={totals} onChanged={() => void load()} />

      <div className="grid gap-4 lg:grid-cols-2">
        <AgentActionConsole
          title="Yuki — Hardware"
          description="Architecture, BOM, sourcing"
          fields={[
            {
              name: "instruction",
              label: "Instruction",
              type: "textarea",
              required: true,
              rows: 3,
              placeholder: "Propose une caméra HD compatible Pi 5…",
            },
          ]}
          onSubmit={(v) => hardwareInstruction(v.instruction)}
        />
        <AgentActionConsole
          title="Zara — Embedded"
          fields={[
            {
              name: "instruction",
              label: "Instruction",
              type: "textarea",
              required: true,
              rows: 3,
              placeholder: "Prépare le script status.py pour le Pi…",
            },
          ]}
          onSubmit={(v) => embeddedInstruction(v.instruction)}
        />
        <AgentActionConsole
          title="Zara — Commande SSH Pi"
          description={piBridge.configured ? "PI_HOST configuré" : "Indisponible tant que PI_HOST n'est pas dans .env"}
          fields={[
            {
              name: "command",
              label: "Commande",
              required: true,
              placeholder: "uname -a",
            },
          ]}
          onSubmit={(v) => embeddedPiCommand(v.command)}
        />
        <AgentActionConsole
          title="Vague B — Probes lab / BOM / vision"
          description="Données réelles ou vide honnête — jamais de fake bancs"
          fields={[
            {
              name: "action",
              label: "Probe",
              type: "select",
              defaultValue: "qa_lab",
              options: [
                { value: "qa_lab", label: "Bilal — lab tests" },
                { value: "safety_lab", label: "Clara — lab + builds" },
                { value: "mech_bom", label: "Ravi — BOM mécanique" },
                { value: "vision_pi", label: "Sana — Pi probe" },
              ],
            },
          ]}
          submitLabel="Lancer probe"
          onSubmit={async (v) => {
            const a = v.action || "qa_lab";
            if (a === "safety_lab") return safetyLabContext();
            if (a === "mech_bom") return mechanicalBomContext();
            if (a === "vision_pi") return visionAiPiProbe("uname -a");
            return qaRobotLabContext();
          }}
        />
      </div>
    </section>
  );
}

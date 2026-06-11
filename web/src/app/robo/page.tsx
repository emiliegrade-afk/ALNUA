"use client";

import { useCallback, useEffect, useState } from "react";
import { AgentCard } from "@/components/shared/agent-card";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchBomEve, fetchEveStatus } from "@/lib/lobby-api";
import { cn } from "@/lib/utils";

const ROBO_AGENTS = [
  {
    icon: "🔧",
    name: "Hardware Agent",
    role: "Hardware",
    branch: "robo" as const,
    description: "BOM, composants et architecture matérielle Eve.",
    skills: ["BOM", "PCB", "Sourcing"],
  },
  {
    icon: "⚡",
    name: "Embedded Dev",
    role: "Firmware",
    branch: "robo" as const,
    description: "Raspberry Pi, firmware et déploiements.",
    skills: ["Python", "Pi", "SSH"],
  },
];

export default function RoboPage() {
  const [bom, setBom] = useState<
    Array<{
      id: string;
      name: string;
      category: string;
      quantity: number;
      unit_cost: number;
      status: string;
    }>
  >([]);
  const [eveStatus, setEveStatus] = useState<{
    connected: boolean;
    battery?: number | null;
  }>({ connected: false });
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const [bomData, status] = await Promise.all([
      fetchBomEve(),
      fetchEveStatus(),
    ]);
    setBom(bomData);
    setEveStatus(status);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 60_000);
    return () => clearInterval(interval);
  }, [load]);

  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="robo"
        title="Pôle Robotique"
        subtitle="Eve Robot · Raspberry Pi · Hardware"
      />

      <section className="mb-8 grid gap-4 sm:grid-cols-2">
        {ROBO_AGENTS.map((agent) => (
          <AgentCard key={agent.name} {...agent} />
        ))}
      </section>

      <div className="mb-8 grid gap-4 sm:grid-cols-2">
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="font-title text-base text-ivory">Eve Robot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <span className="badge-copper px-2 py-0.5 text-xs">
              Prototype
            </span>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  eveStatus.connected ? "bg-copper-light" : "bg-red-500"
                )}
              />
              <span className="font-body text-sm text-titanium">
                Pi {eveStatus.connected ? "online" : "offline"}
              </span>
              {eveStatus.battery != null ? (
                <span className="text-xs text-gray-500">
                  · {eveStatus.battery}% batterie
                </span>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="font-title text-base text-ivory">Looking Glass</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="badge-titanium px-2 py-0.5 text-xs">
              À démarrer
            </span>
          </CardContent>
        </Card>
      </div>

      <section className="mb-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="label-caps">BOM Eve</h2>
          <Button size="sm" variant="outline" className="border-copper/30 hover:border-copper/50">
            Ajouter composant
          </Button>
        </div>
        <div className="overflow-x-auto rounded-xl border border-copper/10">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-copper/10 text-left font-body text-xs text-titanium/60">
                <th className="px-4 py-3">Composant</th>
                <th className="px-4 py-3">Catégorie</th>
                <th className="px-4 py-3">Qté</th>
                <th className="px-4 py-3">Coût unit.</th>
                <th className="px-4 py-3">Statut</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                    Chargement…
                  </td>
                </tr>
              ) : bom.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                    Aucun composant dans la BOM.
                  </td>
                </tr>
              ) : (
                bom.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-copper/10 font-body text-ivory/80"
                  >
                    <td className="px-4 py-3">{row.name}</td>
                    <td className="px-4 py-3 text-titanium">{row.category}</td>
                    <td className="px-4 py-3">{row.quantity}</td>
                    <td className="px-4 py-3">${row.unit_cost.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className="badge-copper px-2 py-0.5 text-xs">
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <Card className="border-copper/20 bg-obsidian-2/90">
        <CardHeader className="pb-2">
          <CardTitle className="font-title text-base text-ivory">Pi Status</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-xs font-medium",
                eveStatus.connected
                  ? "badge-copper"
                  : "bg-red-500/10 text-red-400"
              )}
            >
              {eveStatus.connected ? "Online" : "Offline"}
            </span>
          </div>
          <p className="font-body text-xs text-titanium/60">Dernier ping via API /eve/status</p>
        </CardContent>
      </Card>
    </>
  );
}

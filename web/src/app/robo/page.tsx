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
        <Card className="border-blue-500/20 bg-[#111827]/80">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-white">Eve Robot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400">
              Prototype
            </span>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  eveStatus.connected ? "bg-emerald-500" : "bg-red-500"
                )}
              />
              <span className="text-sm text-gray-400">
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

        <Card className="border-blue-500/20 bg-[#111827]/80">
          <CardHeader className="pb-2">
            <CardTitle className="text-base text-white">Looking Glass</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="rounded-full bg-gray-500/10 px-2 py-0.5 text-xs text-gray-400">
              À démarrer
            </span>
          </CardContent>
        </Card>
      </div>

      <section className="mb-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium uppercase tracking-widest text-gray-500">
            BOM Eve
          </h2>
          <Button size="sm" variant="outline" className="border-blue-500/30">
            Ajouter composant
          </Button>
        </div>
        <div className="overflow-x-auto rounded-xl border border-white/5">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-left text-xs text-gray-500">
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
                    className="border-b border-white/5 text-gray-300"
                  >
                    <td className="px-4 py-3">{row.name}</td>
                    <td className="px-4 py-3 text-gray-500">{row.category}</td>
                    <td className="px-4 py-3">{row.quantity}</td>
                    <td className="px-4 py-3">${row.unit_cost.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400">
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

      <Card className="border-blue-500/20 bg-[#111827]/80">
        <CardHeader className="pb-2">
          <CardTitle className="text-base text-white">Pi Status</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-xs font-medium",
                eveStatus.connected
                  ? "bg-emerald-500/10 text-emerald-400"
                  : "bg-red-500/10 text-red-400"
              )}
            >
              {eveStatus.connected ? "Online" : "Offline"}
            </span>
          </div>
          <p className="text-xs text-gray-500">Dernier ping via API /eve/status</p>
        </CardContent>
      </Card>
    </>
  );
}

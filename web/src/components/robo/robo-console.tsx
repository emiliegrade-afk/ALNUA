"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { AgentActionConsole } from "@/components/shared/agent-action-console";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  createBomItem,
  deleteBomItem,
  embeddedInstruction,
  embeddedPiCommand,
  fetchBomItems,
  fetchEveStatus,
  fetchLookingGlassStatus,
  hardwareInstruction,
  type BomItem,
} from "@/lib/pole-api";
import { cn } from "@/lib/utils";

const CATEGORIES = [
  "vision",
  "audio",
  "moteur",
  "alimentation",
  "microcontroleur",
  "chassis",
  "compute",
  "autre",
];

export function RoboConsole() {
  const [items, setItems] = useState<BomItem[]>([]);
  const [totals, setTotals] = useState({ total_eur: 0, count: 0 });
  const [loading, setLoading] = useState(true);
  const [eveStatus, setEveStatus] = useState({ connected: false, battery: null as number | null });
  const [lgStatus, setLgStatus] = useState({
    connected: false,
    holoplay_running: false,
    message: "",
  });
  const [showAdd, setShowAdd] = useState(false);
  const [newItem, setNewItem] = useState({
    component: "",
    category: "autre",
    quantity: "1",
    unit_price: "",
    status: "a_commander",
  });

  const load = useCallback(async () => {
    setLoading(true);
    const [bom, eve, lg] = await Promise.all([
      fetchBomItems().catch(() => ({ items: [], totals: { total_eur: 0, count: 0, by_category: {} } })),
      fetchEveStatus(),
      fetchLookingGlassStatus().catch(() => ({
        connected: false,
        holoplay_running: false,
        message: "Indisponible",
      })),
    ]);
    setItems(bom.items);
    setTotals({ total_eur: bom.totals.total_eur, count: bom.totals.count });
    setEveStatus({ connected: eve.connected, battery: eve.battery ?? null });
    setLgStatus(lg);
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
    const interval = setInterval(load, 60_000);
    return () => clearInterval(interval);
  }, [load]);

  async function handleAdd() {
    if (!newItem.component.trim()) {
      toast.error("Nom du composant requis");
      return;
    }
    try {
      await createBomItem({
        component: newItem.component,
        category: newItem.category,
        quantity: parseInt(newItem.quantity, 10) || 1,
        unit_price: newItem.unit_price ? parseFloat(newItem.unit_price) : null,
        status: newItem.status,
      });
      toast.success("Composant ajouté");
      setShowAdd(false);
      setNewItem({ component: "", category: "autre", quantity: "1", unit_price: "", status: "a_commander" });
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteBomItem(id);
      toast.success("Supprimé");
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  }

  return (
    <section className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="font-title text-base text-ivory">Eve Pi</CardTitle>
          </CardHeader>
          <CardContent>
            <span
              className={cn(
                "inline-flex items-center gap-2 text-sm",
                eveStatus.connected ? "text-copper-light" : "text-red-400"
              )}
            >
              <span className={cn("h-2 w-2 rounded-full", eveStatus.connected ? "bg-copper-light" : "bg-red-500")} />
              {eveStatus.connected ? "Online" : "Offline"}
              {eveStatus.battery != null ? ` · ${eveStatus.battery}%` : ""}
            </span>
          </CardContent>
        </Card>
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader className="pb-2">
            <CardTitle className="font-title text-base text-ivory">Looking Glass</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <span
              className={
                lgStatus.connected
                  ? "badge-copper px-2 py-0.5 text-xs"
                  : "badge-titanium px-2 py-0.5 text-xs"
              }
            >
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

      <div className="grid gap-4 lg:grid-cols-2">
        <AgentActionConsole
          title="Viktor — Hardware"
          description="BOM, sourcing, architecture matérielle Eve"
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
          title="Rin — Embedded Dev"
          fields={[
            {
              name: "instruction",
              label: "Instruction",
              type: "textarea",
              required: true,
              rows: 3,
              placeholder: "Déploie le script status.py sur le Pi…",
            },
          ]}
          onSubmit={(v) => embeddedInstruction(v.instruction)}
        />
        <AgentActionConsole
          title="Rin — Commande SSH Pi"
          fields={[
            {
              name: "command",
              label: "Commande",
              required: true,
              placeholder: "python3 /home/pi/eve/status.py",
            },
          ]}
          onSubmit={(v) => embeddedPiCommand(v.command)}
        />
      </div>

      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="label-caps">BOM Eve</h2>
          <Button
            size="sm"
            variant="outline"
            className="border-copper/30"
            onClick={() => setShowAdd((s) => !s)}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Ajouter composant
          </Button>
        </div>

        {showAdd ? (
          <Card className="mb-4 border-copper/20 bg-obsidian-2/90">
            <CardContent className="grid gap-3 pt-4 sm:grid-cols-2 lg:grid-cols-5">
              <Input
                placeholder="Composant *"
                value={newItem.component}
                onChange={(e) => setNewItem((n) => ({ ...n, component: e.target.value }))}
                className="border-copper/15 bg-white/[0.02]"
              />
              <Select
                value={newItem.category}
                onValueChange={(v) => setNewItem((n) => ({ ...n, category: v }))}
              >
                <SelectTrigger className="border-copper/15">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                type="number"
                placeholder="Qté"
                value={newItem.quantity}
                onChange={(e) => setNewItem((n) => ({ ...n, quantity: e.target.value }))}
                className="border-copper/15 bg-white/[0.02]"
              />
              <Input
                type="number"
                placeholder="Prix unit. €"
                value={newItem.unit_price}
                onChange={(e) => setNewItem((n) => ({ ...n, unit_price: e.target.value }))}
                className="border-copper/15 bg-white/[0.02]"
              />
              <Button size="sm" onClick={handleAdd} className="bg-copper/20 hover:bg-copper/30">
                Enregistrer
              </Button>
            </CardContent>
          </Card>
        ) : null}

        <div className="overflow-x-auto rounded-xl border border-copper/10">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-copper/10 text-left text-xs text-titanium/60">
                <th className="px-4 py-3">Composant</th>
                <th className="px-4 py-3">Catégorie</th>
                <th className="px-4 py-3">Qté</th>
                <th className="px-4 py-3">Coût unit.</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center">
                    <Loader2 className="mx-auto h-5 w-5 animate-spin text-copper" />
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-titanium/60">
                    Aucun composant — ajoute le premier.
                  </td>
                </tr>
              ) : (
                items.map((row) => (
                  <tr key={row.id} className="border-b border-copper/10 text-ivory/80">
                    <td className="px-4 py-3">{row.component}</td>
                    <td className="px-4 py-3 text-titanium">{row.category}</td>
                    <td className="px-4 py-3">{row.quantity}</td>
                    <td className="px-4 py-3">
                      {row.unit_price != null ? `${row.unit_price.toFixed(2)} €` : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span className="badge-copper px-2 py-0.5 text-xs">{row.status}</span>
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-red-400 hover:text-red-300"
                        onClick={() => handleDelete(row.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

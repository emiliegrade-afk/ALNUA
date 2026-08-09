"use client";

import { useState } from "react";
import { Loader2, Plus, Trash2, Wrench, Search, Network } from "lucide-react";
import { toast } from "sonner";
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
  eveAlternatives,
  eveAssemblyPlan,
  eveInfraBlueprint,
  type BomItem,
  type BomTotals,
} from "@/lib/pole-api";

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

export function EveBomPanel({
  items,
  totals,
  onChanged,
}: {
  items: BomItem[];
  totals: BomTotals;
  onChanged: () => void;
}) {
  const [showAdd, setShowAdd] = useState(false);
  const [newItem, setNewItem] = useState({
    component: "",
    category: "autre",
    quantity: "1",
    unit_price: "",
    status: "a_commander",
  });
  const [need, setNeed] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [report, setReport] = useState<string>("");

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
      toast.success("Composant ajouté au BOM");
      setShowAdd(false);
      setNewItem({ component: "", category: "autre", quantity: "1", unit_price: "", status: "a_commander" });
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteBomItem(id);
      toast.success("Supprimé");
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  }

  async function runAlternatives() {
    if (need.trim().length < 3) {
      toast.error("Décris le besoin (ex. caméra depth Pi 5)");
      return;
    }
    setBusy("alt");
    try {
      const r = await eveAlternatives(need.trim());
      const opts = (r.options as Array<Record<string, unknown>>) || [];
      const lines = [
        `## Alternatives — ${String(r.need || need)}`,
        r.recommendation ? `Reco : ${String(r.recommendation)}` : "",
        ...opts.map(
          (o, i) =>
            `${i + 1}. [${String(o.tier)}] ${String(o.name)} — ~${String(o.approx_price_eur)}€ (${String(o.supplier_hint)})\n   ${String(o.why_cheaper_or_better || "")}`,
        ),
        r.disclaimer ? `\n_${String(r.disclaimer)}_` : "",
      ];
      setReport(lines.filter(Boolean).join("\n"));
      toast.success("Alternatives générées (à vérifier avant achat)");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur IA");
    } finally {
      setBusy(null);
    }
  }

  async function runAssembly() {
    setBusy("asm");
    try {
      const r = await eveAssemblyPlan(need.trim() || "Assembler Eve selon le BOM actuel");
      const steps = (r.steps as Array<Record<string, unknown>>) || [];
      const lines = [
        `## ${String(r.title || "Plan de montage")}`,
        ...(r.prerequisites as string[] | undefined)?.map((p) => `- Prérequis : ${p}`) ?? [],
        ...steps.map(
          (s) =>
            `### ${String(s.order)}. ${String(s.title)}\nPièces : ${JSON.stringify(s.parts)}\nActions : ${JSON.stringify(s.actions)}\nChecks : ${JSON.stringify(s.checks)}`,
        ),
        r.wiring_notes ? `\nCâblage : ${String(r.wiring_notes)}` : "",
        r.next_software ? `\nEnsuite (embedded) : ${String(r.next_software)}` : "",
      ];
      setReport(lines.filter(Boolean).join("\n"));
      toast.success("Plan de montage prêt");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur IA");
    } finally {
      setBusy(null);
    }
  }

  async function runInfra() {
    setBusy("infra");
    try {
      const r = await eveInfraBlueprint("full");
      setReport(
        [
          "## Qui fait quoi — Eve",
          String(r.summary_for_emilie || ""),
          "",
          "Robot physique → hardware / electronics / mechanical / firmware / embedded",
          "App compagnon (comme Naïa) → dev_app / dev_backend — ne soude pas le robot",
          r.pi_status_policy ? `\nPi : ${String(r.pi_status_policy)}` : "",
        ].join("\n"),
      );
      toast.success("Blueprint rôles généré");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur IA");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="border-copper/20 bg-obsidian-2/90">
        <CardHeader className="pb-2">
          <CardTitle className="font-title text-base text-ivory">
            BOM Eve — {totals.count} pièces · {totals.total_eur.toFixed(2)} €
          </CardTitle>
          <p className="text-xs text-titanium/60">
            Saisie manuelle ici. Les agents proposent alternatives / montage — jamais d&apos;achat auto.
            Pi plus tard : le Hub utilisera SSH (`PI_HOST`), pas WinSCP.
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" className="border-copper/30" onClick={() => setShowAdd((s) => !s)}>
              <Plus className="mr-1 h-3.5 w-3.5" /> Ajouter composant
            </Button>
            <Button size="sm" variant="outline" className="border-copper/30" disabled={!!busy} onClick={() => void runAlternatives()}>
              {busy === "alt" ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : <Search className="mr-1 h-3.5 w-3.5" />}
              Alternatives (Marco)
            </Button>
            <Button size="sm" variant="outline" className="border-copper/30" disabled={!!busy} onClick={() => void runAssembly()}>
              {busy === "asm" ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : <Wrench className="mr-1 h-3.5 w-3.5" />}
              Plan de montage (Ravi)
            </Button>
            <Button size="sm" variant="outline" className="border-copper/30" disabled={!!busy} onClick={() => void runInfra()}>
              {busy === "infra" ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : <Network className="mr-1 h-3.5 w-3.5" />}
              Qui build quoi (Yuki)
            </Button>
          </div>
          <Input
            placeholder="Besoin pour alternatives / objectif montage (ex. caméra depth, bras servo…)"
            value={need}
            onChange={(e) => setNeed(e.target.value)}
            className="border-copper/15 bg-obsidian-deep/40"
          />

          {showAdd ? (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
              <Input
                placeholder="Composant *"
                value={newItem.component}
                onChange={(e) => setNewItem((n) => ({ ...n, component: e.target.value }))}
                className="border-copper/15 bg-obsidian-deep/40"
              />
              <Select value={newItem.category} onValueChange={(v) => setNewItem((n) => ({ ...n, category: v }))}>
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
                className="border-copper/15 bg-obsidian-deep/40"
              />
              <Input
                type="number"
                placeholder="Prix unit. €"
                value={newItem.unit_price}
                onChange={(e) => setNewItem((n) => ({ ...n, unit_price: e.target.value }))}
                className="border-copper/15 bg-obsidian-deep/40"
              />
              <Button size="sm" onClick={() => void handleAdd()} className="bg-copper/20 hover:bg-copper/30">
                Enregistrer
              </Button>
            </div>
          ) : null}

          <ul className="max-h-48 space-y-1 overflow-y-auto text-sm">
            {items.length === 0 ? (
              <li className="text-titanium/50">BOM vide — ajoute Pi, alim, 1 capteur pour démarrer.</li>
            ) : (
              items.map((it) => (
                <li key={it.id} className="flex items-center justify-between gap-2 rounded border border-copper/10 px-2 py-1">
                  <span className="truncate text-ivory">
                    {it.component}{" "}
                    <span className="text-titanium/50">
                      ×{it.quantity} · {it.category}
                      {it.unit_price != null ? ` · ${it.unit_price}€` : ""}
                    </span>
                  </span>
                  <button type="button" onClick={() => void handleDelete(it.id)} className="text-titanium/40 hover:text-red-400" aria-label="Supprimer">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </li>
              ))
            )}
          </ul>

          {report ? (
            <pre className="alnua-scroll max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-copper/15 bg-obsidian-deep/50 p-3 text-[11px] text-ivory/90">
              {report}
            </pre>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

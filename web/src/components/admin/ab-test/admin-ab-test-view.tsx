"use client";

import { useState } from "react";
import { Loader2, Play } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  runQuickCompare,
  type ABTestRunResult,
} from "@/lib/admin-ab-test-api";

const DEFAULT_KWARGS_A = '{\n  "instruction": "Résume les priorités du jour en 3 bullets."\n}';
const DEFAULT_KWARGS_B =
  '{\n  "instruction": "Liste les 3 priorités du jour — ton direct, pas de blabla."\n}';

function parseJsonObject(raw: string, label: string): Record<string, unknown> | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      toast.error(`${label} doit être un objet JSON`);
      return null;
    }
    return parsed as Record<string, unknown>;
  } catch {
    toast.error(`${label} : JSON invalide`);
    return null;
  }
}

export function AdminAbTestView() {
  const [agentId, setAgentId] = useState("qa");
  const [method, setMethod] = useState("handle_instruction");
  const [kwargsA, setKwargsA] = useState(DEFAULT_KWARGS_A);
  const [kwargsB, setKwargsB] = useState(DEFAULT_KWARGS_B);
  const [criteria, setCriteria] = useState(
    "Lequel est le plus utile, précis et bien structuré ?"
  );
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ABTestRunResult | null>(null);
  const [history, setHistory] = useState<ABTestRunResult[]>([]);

  async function handleRun() {
    const parsedA = parseJsonObject(kwargsA, "Variant A");
    const parsedB = parseJsonObject(kwargsB, "Variant B");
    if (!parsedA || !parsedB) return;

    setRunning(true);
    setResult(null);
    try {
      const out = await runQuickCompare({
        agent_id: agentId.trim(),
        method: method.trim(),
        kwargs_a: parsedA,
        kwargs_b: parsedB,
        criteria: criteria.trim(),
      });
      setResult(out);
      setHistory((prev) => [out, ...prev].slice(0, 10));
      toast.success(`Gagnant : ${out.winner}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur A/B test");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="border-amber-500/20 bg-amber-500/5">
        <CardContent className="pt-6 font-body text-sm text-amber-100/90">
          Lance un vrai appel agent + juge LLM (Alex). Coûte des tokens — usage
          ponctuel recommandé.
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <Label htmlFor="ab-agent">Agent</Label>
            <Input
              id="ab-agent"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              className="mt-1 border-copper/20 bg-obsidian-2"
            />
          </div>
          <div>
            <Label htmlFor="ab-method">Méthode</Label>
            <Input
              id="ab-method"
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="mt-1 border-copper/20 bg-obsidian-2"
            />
          </div>
          <div>
            <Label htmlFor="ab-criteria">Critères juge</Label>
            <Input
              id="ab-criteria"
              value={criteria}
              onChange={(e) => setCriteria(e.target.value)}
              className="mt-1 border-copper/20 bg-obsidian-2"
            />
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <Label htmlFor="ab-kwargs-a">kwargs variant A (JSON)</Label>
            <textarea
              id="ab-kwargs-a"
              value={kwargsA}
              onChange={(e) => setKwargsA(e.target.value)}
              rows={5}
              className="mt-1 w-full rounded-lg border border-copper/20 bg-obsidian-2 p-2 font-mono text-xs text-titanium"
            />
          </div>
          <div>
            <Label htmlFor="ab-kwargs-b">kwargs variant B (JSON)</Label>
            <textarea
              id="ab-kwargs-b"
              value={kwargsB}
              onChange={(e) => setKwargsB(e.target.value)}
              rows={5}
              className="mt-1 w-full rounded-lg border border-copper/20 bg-obsidian-2 p-2 font-mono text-xs text-titanium"
            />
          </div>
        </div>
      </div>

      <Button
        type="button"
        onClick={() => void handleRun()}
        disabled={running}
        className="bg-copper/20 text-ivory hover:bg-copper/30"
      >
        {running ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Play className="mr-2 h-4 w-4" />
        )}
        Lancer quick-compare
      </Button>

      {result && (
        <Card className="border-copper/20 bg-obsidian-2/80">
          <CardHeader>
            <CardTitle className="font-title text-base text-ivory">
              Résultat — gagnant{" "}
              <span className="text-copper-light">{result.winner}</span>
              {result.confidence > 0 && (
                <span className="ml-2 text-sm font-normal text-titanium/60">
                  ({Math.round(result.confidence * 100)}% confiance)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 font-body text-sm text-titanium">
            <p>{result.judge_reasoning || result.judgment?.reasoning}</p>
            <p className="text-xs text-titanium/50">
              {result.variant_a_label} vs {result.variant_b_label} ·{" "}
              {result.duration_ms}ms
            </p>
          </CardContent>
        </Card>
      )}

      {history.length > 1 && (
        <Card className="border-copper/10 bg-obsidian-2/60">
          <CardHeader>
            <CardTitle className="font-body text-sm text-titanium/70">
              Session (local)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 font-body text-xs text-titanium/60">
            {history.slice(1).map((h, i) => (
              <p key={`${h.name}-${i}`}>
                {h.name} → {h.winner}
              </p>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

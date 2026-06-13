"use client";

import Link from "next/link";
import { AgentActionConsole } from "@/components/shared/agent-action-console";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  marketingCreateContent,
  marketingInstruction,
  marketingSeoAudit,
  runAnalyticsCycle,
  runPublisherCycle,
  syncStoreReviews,
} from "@/lib/pole-api";
import { toast } from "sonner";
import { useState } from "react";
import { Loader2 } from "lucide-react";

export function MarketingConsole() {
  const [botLoading, setBotLoading] = useState<string | null>(null);

  async function runBot(name: string, fn: () => Promise<unknown>) {
    setBotLoading(name);
    try {
      const result = await fn();
      toast.success(JSON.stringify(result));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setBotLoading(null);
    }
  }

  return (
    <section className="space-y-6">
      <h2 className="label-caps">Console Marketing</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <AgentActionConsole
          title="Lena — Instruction libre"
          fields={[
            {
              name: "instruction",
              label: "Instruction",
              type: "textarea",
              required: true,
              rows: 4,
              placeholder: "Audit SEO wyrdheim.com, veille concurrentielle…",
            },
          ]}
          onSubmit={(v) => marketingInstruction(v.instruction)}
        />
        <AgentActionConsole
          title="Audit SEO"
          fields={[
            {
              name: "url",
              label: "URL",
              required: true,
              placeholder: "https://wyrdheim.com",
            },
          ]}
          onSubmit={(v) => marketingSeoAudit(v.url)}
        />
        <AgentActionConsole
          title="Générer du contenu"
          fields={[
            {
              name: "type",
              label: "Format",
              type: "select",
              defaultValue: "discord",
              options: [
                { value: "discord", label: "Discord" },
                { value: "twitter", label: "Twitter/X" },
                { value: "changelog", label: "Changelog" },
              ],
            },
            {
              name: "project",
              label: "Projet",
              type: "select",
              defaultValue: "wyrdheim",
              options: [
                { value: "wyrdheim", label: "Wyrdheim" },
                { value: "naia", label: "Naïa" },
                { value: "eve", label: "Eve" },
              ],
            },
            { name: "topic", label: "Sujet", required: true },
            {
              name: "tone",
              label: "Ton",
              type: "select",
              defaultValue: "épique",
              options: [
                { value: "épique", label: "Épique" },
                { value: "informatif", label: "Informatif" },
                { value: "bienveillant", label: "Bienveillant" },
              ],
            },
          ]}
          onSubmit={(v) =>
            marketingCreateContent({
              type: v.type,
              project: v.project,
              topic: v.topic,
              tone: v.tone,
            })
          }
        />
      </div>

      <Card className="border-copper/20 bg-obsidian-2/90">
        <CardHeader className="pb-2">
          <CardTitle className="font-title text-base text-ivory">Bots automatisés</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            className="border-copper/30"
            disabled={!!botLoading}
            onClick={() => runBot("reviews", () => syncStoreReviews())}
          >
            {botLoading === "reviews" ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : null}
            Sync reviews stores
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-copper/30"
            disabled={!!botLoading}
            onClick={() => runBot("publisher", runPublisherCycle)}
          >
            {botLoading === "publisher" ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : null}
            Publisher cycle
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-copper/30"
            disabled={!!botLoading}
            onClick={() => runBot("analytics", runAnalyticsCycle)}
          >
            {botLoading === "analytics" ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : null}
            Analytics sync
          </Button>
          <Button asChild size="sm" variant="ghost">
            <Link href="/content">Queue de posts</Link>
          </Button>
        </CardContent>
      </Card>
    </section>
  );
}

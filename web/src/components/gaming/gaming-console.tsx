"use client";

import { AgentActionConsole } from "@/components/shared/agent-action-console";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  devGamingInstruction,
  levelDesignerBalance,
  levelDesignerLevel,
  levelDesignerLore,
  levelDesignerQuest,
} from "@/lib/pole-api";
import { fetchUe58Status, type Ue58Status } from "@/lib/gaming-ue58";
import { useEffect, useState } from "react";

export function GamingConsole() {
  const [ue58, setUe58] = useState<Ue58Status | null>(null);

  useEffect(() => {
    fetchUe58Status()
      .then(setUe58)
      .catch(() =>
        setUe58({
          ok: false,
          configured: false,
          connected: false,
          error: "Statut UE5.8 indisponible",
        }),
      );
  }, []);

  const statusLabel = !ue58
    ? "…"
    : ue58.connected
      ? "Connecté"
      : !ue58.configured
        ? "Hors ligne — définir UE5_SERVER_URL (ou UE58_HOST)"
        : ue58.error || "Serveur UE5.8 injoignable";

  return (
    <section className="space-y-6">
      <h2 className="label-caps">Console agents Gaming</h2>

      <Card className="border-copper/20 bg-obsidian-2/90">
        <CardHeader className="pb-2">
          <CardTitle className="font-title text-base text-ivory">
            Pont UE5.8 (DEC-017)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <span
            className={
              ue58?.connected
                ? "badge-copper px-2 py-0.5 text-xs"
                : "badge-titanium px-2 py-0.5 text-xs"
            }
          >
            {statusLabel}
          </span>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <AgentActionConsole
          title="Suki — Dev Gaming"
          description="UE5.8, blueprints, intégrations studio"
          fields={[
            {
              name: "instruction",
              label: "Instruction",
              type: "textarea",
              required: true,
              rows: 4,
              placeholder: "Optimise le blueprint de mouvement du personnage…",
            },
          ]}
          submitLabel="Envoyer à Dev Gaming"
          onSubmit={(v) => devGamingInstruction(v.instruction)}
        />
        <AgentActionConsole
          title="Finn — Générer une quête"
          fields={[
            { name: "quest_name", label: "Nom de la quête", required: true },
            {
              name: "game",
              label: "Jeu",
              defaultValue: "Wyrdheim Online",
              required: true,
            },
            {
              name: "lore_context",
              label: "Contexte lore",
              type: "textarea",
              rows: 3,
            },
            {
              name: "quest_type",
              label: "Type",
              type: "select",
              defaultValue: "main",
              options: [
                { value: "main", label: "Main" },
                { value: "side", label: "Side" },
                { value: "daily", label: "Daily" },
              ],
            },
          ]}
          onSubmit={(v) =>
            levelDesignerQuest({
              quest_name: v.quest_name,
              game: v.game,
              lore_context: v.lore_context,
              quest_type: v.quest_type,
              player_level_range: "1-10",
            })
          }
        />
        <AgentActionConsole
          title="Finn — Lore Database"
          fields={[
            { name: "subject", label: "Sujet", required: true },
            { name: "game", label: "Jeu", defaultValue: "Wyrdheim Online", required: true },
            {
              name: "lore_type",
              label: "Type",
              type: "select",
              defaultValue: "history",
              options: [
                { value: "history", label: "Histoire" },
                { value: "character", label: "Personnage" },
                { value: "location", label: "Lieu" },
                { value: "item", label: "Objet" },
              ],
            },
          ]}
          onSubmit={(v) =>
            levelDesignerLore({
              subject: v.subject,
              game: v.game,
              lore_type: v.lore_type,
            })
          }
        />
        <AgentActionConsole
          title="Finn — Level Design"
          fields={[
            { name: "level_name", label: "Niveau", required: true },
            { name: "game", label: "Jeu", defaultValue: "Wyrdheim Online", required: true },
            { name: "biome", label: "Biome" },
            {
              name: "difficulty",
              label: "Difficulté",
              type: "select",
              defaultValue: "medium",
              options: [
                { value: "easy", label: "Facile" },
                { value: "medium", label: "Moyen" },
                { value: "hard", label: "Difficile" },
              ],
            },
          ]}
          onSubmit={(v) =>
            levelDesignerLevel({
              level_name: v.level_name,
              game: v.game,
              biome: v.biome,
              difficulty: v.difficulty,
            })
          }
        />
        <AgentActionConsole
          title="Finn — Balance review"
          fields={[
            { name: "system", label: "Système", required: true, placeholder: "combat, loot…" },
            {
              name: "current_values",
              label: "Valeurs actuelles (JSON)",
              type: "textarea",
              required: true,
              defaultValue: "{}",
              rows: 3,
            },
            { name: "player_feedback", label: "Feedback joueurs", type: "textarea", rows: 2 },
          ]}
          onSubmit={(v) => {
            let parsed: Record<string, unknown> = {};
            try {
              parsed = JSON.parse(v.current_values || "{}") as Record<string, unknown>;
            } catch {
              parsed = { raw: v.current_values };
            }
            return levelDesignerBalance({
              system: v.system,
              current_values: parsed,
              player_feedback: v.player_feedback,
            });
          }}
        />
      </div>
    </section>
  );
}

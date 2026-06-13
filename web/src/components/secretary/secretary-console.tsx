"use client";

import { AgentActionConsole } from "@/components/shared/agent-action-console";
import {
  secretaryDraftContract,
  secretaryDraftEmail,
  secretaryMeetingNotes,
  secretaryPlanMeeting,
  secretaryTriageEmails,
} from "@/lib/pole-api";

export function SecretaryConsole() {
  return (
    <section className="space-y-6">
      <h2 className="label-caps">Console Nadia — Secrétariat</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <AgentActionConsole
          title="Rédiger un email"
          fields={[
            { name: "recipient", label: "Destinataire", required: true },
            { name: "subject", label: "Objet", required: true },
            {
              name: "context",
              label: "Contexte / contenu",
              type: "textarea",
              required: true,
              rows: 4,
            },
            {
              name: "tone",
              label: "Ton",
              type: "select",
              defaultValue: "professionnel",
              options: [
                { value: "professionnel", label: "Professionnel" },
                { value: "chaleureux", label: "Chaleureux" },
                { value: "formel", label: "Formel" },
                { value: "direct", label: "Direct" },
              ],
            },
          ]}
          onSubmit={(v) =>
            secretaryDraftEmail({
              recipient: v.recipient,
              subject: v.subject,
              context: v.context,
              tone: v.tone,
            })
          }
        />
        <AgentActionConsole
          title="Trier les emails"
          description="Colle un email par bloc : FROM / SUBJECT / BODY"
          fields={[
            {
              name: "from",
              label: "De",
              required: true,
              placeholder: "client@example.com",
            },
            { name: "subject", label: "Objet", required: true },
            {
              name: "body",
              label: "Corps",
              type: "textarea",
              required: true,
              rows: 5,
            },
          ]}
          onSubmit={(v) =>
            secretaryTriageEmails([
              { from: v.from, subject: v.subject, body: v.body },
            ])
          }
        />
        <AgentActionConsole
          title="Planifier une réunion"
          fields={[
            {
              name: "participants",
              label: "Participants (virgules)",
              required: true,
              placeholder: "Emilie, Sam, Partenaire X",
            },
            { name: "topic", label: "Sujet", required: true },
            {
              name: "duration_minutes",
              label: "Durée (min)",
              type: "number",
              defaultValue: "60",
            },
            {
              name: "constraints",
              label: "Contraintes horaires",
              type: "textarea",
              rows: 2,
            },
          ]}
          onSubmit={(v) =>
            secretaryPlanMeeting({
              participants: v.participants.split(",").map((p) => p.trim()).filter(Boolean),
              topic: v.topic,
              duration_minutes: parseInt(v.duration_minutes, 10) || 60,
              constraints: v.constraints,
            })
          }
        />
        <AgentActionConsole
          title="Brouillon de contrat"
          fields={[
            {
              name: "contract_type",
              label: "Type",
              required: true,
              placeholder: "NDA, prestation, partenariat…",
            },
            { name: "party_name", label: "Partie contractante", required: true },
            {
              name: "scope",
              label: "Périmètre",
              type: "textarea",
              required: true,
              rows: 3,
            },
            { name: "duration", label: "Durée", required: true, placeholder: "6 mois" },
            { name: "compensation", label: "Rémunération" },
          ]}
          onSubmit={(v) =>
            secretaryDraftContract({
              contract_type: v.contract_type,
              party_name: v.party_name,
              scope: v.scope,
              duration: v.duration,
              compensation: v.compensation,
            })
          }
        />
        <AgentActionConsole
          title="Compte rendu de réunion"
          className="lg:col-span-2"
          fields={[
            { name: "meeting_title", label: "Titre", required: true },
            {
              name: "participants",
              label: "Participants (virgules)",
              required: true,
            },
            {
              name: "raw_notes",
              label: "Notes brutes",
              type: "textarea",
              required: true,
              rows: 6,
            },
          ]}
          onSubmit={(v) =>
            secretaryMeetingNotes({
              meeting_title: v.meeting_title,
              participants: v.participants.split(",").map((p) => p.trim()).filter(Boolean),
              raw_notes: v.raw_notes,
            })
          }
        />
      </div>
    </section>
  );
}

import { describe, expect, it } from "vitest";

import { isInCall } from "@/components/live/live-call-stage";
import { wantsClearScreens } from "@/lib/live-clear";
import { extractOAuthUrl } from "@/lib/live-oauth";
import { workKind, workTitle, WORK_LABEL } from "@/lib/live-work";

describe("parallel work labels", () => {
  it("marks an internet search so it can sit beside other jobs", () => {
    expect(workKind({ agent_id: "secretary", instruction: "Fais une recherche internet sur l'IA" })).toBe(
      "research",
    );
    expect(WORK_LABEL.research).toBe("Recherche internet");
    expect(workTitle({ agent_id: "secretary", instruction: "Veille IA 7 jours" })).toContain(
      "Recherche internet",
    );
  });

  it("keeps mail, agenda and a COO plan in their own buckets", () => {
    expect(workKind({ agent_id: "secretary", instruction: "Résume mes mails" })).toBe("mail");
    expect(workKind({ agent_id: "secretary", instruction: "Quel est mon agenda ?" })).toBe("calendar");
    expect(workKind({ agent_id: "plan", instruction: "Fais tout ça" })).toBe("plan");
    expect(workKind({ agent_id: "coo", instruction: "État du pipeline" })).toBe("other");
    expect(workKind({ agent_id: "secretary", instruction: "Graphique des ventes" })).toBe("chart");
    expect(workKind({ agent_id: "secretary", instruction: "Synthèse du rapport" })).toBe(
      "summary",
    );
  });

  it("treats the green phone as off-hook only after the call is up", () => {
    expect(isInCall("idle")).toBe(false);
    expect(isInCall("connecting")).toBe(false);
    expect(isInCall("ready")).toBe(true);
    expect(isInCall("speaking")).toBe(true);
  });

  it("unwraps a Gmail OAuth reply that mixed hint and URL", () => {
    const wrapped =
      "Connecte-toi avec **alnua.global@gmail.com**\nhttps://connect.composio.dev/link/abc";
    expect(extractOAuthUrl(wrapped)).toBe("https://connect.composio.dev/link/abc");
  });

  it("labels image generation", () => {
    expect(workKind({ agent_id: "secretary", instruction: "Génère une image de robot" })).toBe(
      "image",
    );
  });

  it("labels opening a page so it sits beside research", () => {
    expect(workKind({ agent_id: "secretary", instruction: "Ouvre Instagram" })).toBe(
      "open",
    );
    expect(WORK_LABEL.open).toBe("Ouvrir");
  });

  it("detects tout effacer without matching a search", () => {
    expect(wantsClearScreens("tout effacer")).toBe(true);
    expect(wantsClearScreens("efface l'écran")).toBe(true);
    expect(wantsClearScreens("cherche les actualités")).toBe(false);
  });
});

import { readFileSync } from "fs";
import { join } from "path";
import { describe, expect, it } from "vitest";

/**
 * All primary department routes must be live — never MockupDepartmentPage.
 */
const LIVE_DEPTS = [
  "finances",
  "marketing",
  "rd",
  "app",
  "gaming",
  "robo",
  "ceo",
  "secretary",
  "legal",
  "brand",
  "hub",
  "analytics",
  "hq",
] as const;

describe("department primary routes are live (not MockupShell)", () => {
  for (const dept of LIVE_DEPTS) {
    it(`/${dept} does not mount MockupDepartmentPage`, () => {
      const src = readFileSync(
        join(process.cwd(), "src", "app", dept, "page.tsx"),
        "utf8",
      );
      expect(src).not.toMatch(/MockupDepartmentPage/);
    });
  }

  it("/finances re-exports finances-v2", () => {
    const src = readFileSync(join(process.cwd(), "src", "app", "finances", "page.tsx"), "utf8");
    expect(src).toMatch(/finances-v2/);
  });

  it("/marketing re-exports marketing-v2", () => {
    const src = readFileSync(join(process.cwd(), "src", "app", "marketing", "page.tsx"), "utf8");
    expect(src).toMatch(/marketing-v2/);
  });

  it("/rd keeps deep-link path to RdPageContent", () => {
    const src = readFileSync(join(process.cwd(), "src", "app", "rd", "page.tsx"), "utf8");
    expect(src).toMatch(/RdPageContent/);
    expect(src).toMatch(/rnd-v2/);
  });

  it("/brand uses BrandView", () => {
    const src = readFileSync(join(process.cwd(), "src", "app", "brand", "page.tsx"), "utf8");
    expect(src).toMatch(/BrandView/);
  });

  it("/ceo and /secretary use live panels", () => {
    // Brief + SiegeLifeLinks live inside CeoCommandView / SecretaryCommandView
    // since the siege redesign (2026-08) — checking the command view covers both.
    const ceo = readFileSync(join(process.cwd(), "src", "app", "ceo", "page.tsx"), "utf8");
    const sec = readFileSync(join(process.cwd(), "src", "app", "secretary", "page.tsx"), "utf8");
    expect(ceo).toMatch(/CeoCommandView/);
    expect(sec).toMatch(/NadiaDesktopPanel|NadiaToolsPanel/);
    expect(sec).toMatch(/SecretaryCommandView/);

    const ceoCommandView = readFileSync(
      join(process.cwd(), "src", "components", "siege", "ceo-command-view.tsx"),
      "utf8",
    );
    const secretaryCommandView = readFileSync(
      join(process.cwd(), "src", "components", "siege", "secretary-command-view.tsx"),
      "utf8",
    );
    expect(ceoCommandView).toMatch(/SiegeLifeLinks/);
    expect(secretaryCommandView).toMatch(/SiegeLifeLinks/);
  });

  it("/hub uses direction roster", () => {
    const hub = readFileSync(join(process.cwd(), "src", "app", "hub", "page.tsx"), "utf8");
    expect(hub).toMatch(/BureauRoster/);
    expect(hub).toMatch(/SiegeLifeLinks/);
  });

  it("/lounge is Agent Lounge shell (not OpenRoom repas)", () => {
    const page = readFileSync(join(process.cwd(), "src", "app", "lounge", "page.tsx"), "utf8");
    expect(page).toMatch(/LoungePageClient/);
    const client = readFileSync(
      join(process.cwd(), "src", "app", "lounge", "lounge-page-client.tsx"),
      "utf8",
    );
    expect(client).toMatch(/Agent Lounge/);
    expect(client).toMatch(/LoungeHero/);
    const openroom = readFileSync(
      join(process.cwd(), "src", "app", "openroom", "page.tsx"),
      "utf8",
    );
    expect(openroom).toMatch(/redirect\(`\/lounge/);
  });

  it("/competition shows leaderboard page", () => {
    const page = readFileSync(join(process.cwd(), "src", "app", "competition", "page.tsx"), "utf8");
    expect(page).toMatch(/fetchLeaderboard/);
  });

  it("/legal uses Solène persona + counsel panel", () => {
    const legal = readFileSync(join(process.cwd(), "src", "app", "legal", "page.tsx"), "utf8");
    expect(legal).toMatch(/LegalPersonaCard/);
    expect(legal).toMatch(/LegalCounselPanel/);
  });

  it("/hq uses immersive floor map", () => {
    const hq = readFileSync(join(process.cwd(), "src", "app", "hq", "page.tsx"), "utf8");
    expect(hq).toMatch(/HqFloorMap/);
    expect(hq).not.toMatch(/MockupDirectory/);
  });

  it("/hub and /analytics are live shells", () => {
    const hub = readFileSync(join(process.cwd(), "src", "app", "hub", "page.tsx"), "utf8");
    const analytics = readFileSync(
      join(process.cwd(), "src", "app", "analytics", "page.tsx"),
      "utf8",
    );
    expect(hub).toMatch(/DeptV2PageShell/);
    expect(hub).toMatch(/BureauRoster/);
    expect(analytics).toMatch(/DeptV2PageShell/);
  });
});

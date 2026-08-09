import { readFileSync } from "fs";
import { join } from "path";
import { describe, expect, it } from "vitest";

/**
 * Phase B / BUG-013 — primary department routes must serve live *-v2 shells
 * (or RdPageContent for R&D deep-links), never MockupDepartmentPage.
 */
const LIVE_DEPTS = ["finances", "marketing", "rd", "app", "gaming", "robo"] as const;

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
});

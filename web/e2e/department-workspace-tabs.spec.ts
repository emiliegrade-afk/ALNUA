import { expect, test } from "@playwright/test";

/**
 * Direct precedent: rd-tabs.spec.ts caught a real regression once
 * (tab button looked active but its panel silently failed to mount).
 * Same risk here — DepartmentWorkspace's 3 tabs are new Radix Tabs, not a
 * hand-rolled switcher, but still worth verifying end-to-end in a real
 * browser rather than trusting the component tests alone.
 */
test.describe("DepartmentWorkspace — tab switching", () => {
  test("defaults to Équipe and switches to Projets / Missions", async ({ page }) => {
    await page.goto("/app");

    const equipeTab = page.getByRole("tab", { name: "Équipe" });
    const projetsTab = page.getByRole("tab", { name: "Projets" });
    const missionsTab = page.getByRole("tab", { name: "Missions" });

    await expect(equipeTab).toBeVisible({ timeout: 30_000 });
    await expect(equipeTab).toHaveAttribute("data-state", "active");

    await projetsTab.click();
    await expect(projetsTab).toHaveAttribute("data-state", "active");
    await expect(equipeTab).toHaveAttribute("data-state", "inactive");

    await missionsTab.click();
    await expect(missionsTab).toHaveAttribute("data-state", "active");
  });

  test("keyboard shortcuts 1/2/3 switch tabs", async ({ page }) => {
    await page.goto("/app");
    const missionsTab = page.getByRole("tab", { name: "Missions" });
    await expect(page.getByRole("tab", { name: "Équipe" })).toBeVisible({ timeout: 30_000 });

    // React 18 dev-mode Strict Mode double-invokes effects right after mount
    // (attach → detach → re-attach) — a keypress landing in that brief gap
    // can be missed even though the listener is correctly wired for real
    // usage (prod builds don't double-invoke). Retry instead of a single
    // blind press so the test isn't racing that dev-only window.
    await expect(async () => {
      await page.keyboard.press("3");
      await expect(missionsTab).toHaveAttribute("data-state", "active", { timeout: 1_000 });
    }).toPass({ timeout: 10_000 });

    await expect(async () => {
      await page.keyboard.press("1");
      await expect(page.getByRole("tab", { name: "Équipe" })).toHaveAttribute(
        "data-state",
        "active",
        { timeout: 1_000 }
      );
    }).toPass({ timeout: 10_000 });
  });
});

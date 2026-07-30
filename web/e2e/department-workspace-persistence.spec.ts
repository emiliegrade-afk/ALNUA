import { expect, test } from "@playwright/test";

/**
 * The exact regression the independent Design Review flagged as
 * high-severity: since each department is a distinct Next.js route, a
 * useState-only tab would reset to Équipe every time you navigate away and
 * back — 9x extra clicks/day at real usage volume. The fix is a Zustand
 * store persisted to sessionStorage (department-workspace-store.ts); this
 * verifies the actual navigate-away-and-back flow, not just the store unit.
 */
test.describe("DepartmentWorkspace — tab persistence across department navigation", () => {
  test("remembers Missions on /app after visiting /gaming and coming back", async ({ page }) => {
    await page.goto("/app");
    const appMissionsTab = page.getByRole("tab", { name: "Missions" });
    await expect(appMissionsTab).toBeVisible({ timeout: 30_000 });
    await appMissionsTab.click();
    await expect(appMissionsTab).toHaveAttribute("data-state", "active");

    await page.goto("/gaming");
    await expect(page.getByRole("tab", { name: "Équipe" })).toBeVisible({ timeout: 30_000 });

    await page.goto("/app");
    await expect(page.getByRole("tab", { name: "Missions" })).toHaveAttribute(
      "data-state",
      "active",
      { timeout: 30_000 }
    );
  });

  test("each department keeps its own independent active tab", async ({ page }) => {
    await page.goto("/gaming");
    await expect(page.getByRole("tab", { name: "Équipe" })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("tab", { name: "Projets" }).click();

    await page.goto("/robo");
    await expect(page.getByRole("tab", { name: "Équipe" })).toBeVisible({ timeout: 30_000 });
    // /robo was never visited before — must default to Équipe, not inherit
    // /gaming's "Projets" choice.
    await expect(page.getByRole("tab", { name: "Équipe" })).toHaveAttribute(
      "data-state",
      "active"
    );
  });
});

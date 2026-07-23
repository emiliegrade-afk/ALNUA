import { expect, test } from "@playwright/test";

/**
 * Beyond page-audit.spec.ts's "loads without crashing" smoke check — this
 * verifies the /rd tab switcher actually swaps content, not just that the
 * buttons render. Regressed once already (dynamic-imported tab panels can
 * silently fail to mount while the tab button itself still looks active).
 */
test.describe("Centre R&D — tab switching", () => {
  test("defaults to Brainstorm and switches to Centre R&D + Dossiers", async ({
    page,
  }) => {
    await page.goto("/rd");

    const brainstormTab = page.getByRole("button", { name: "Brainstorm", exact: true });
    const rndTab = page.getByRole("button", { name: "Centre R&D", exact: true });
    const dossiersTab = page.getByRole("button", { name: "Dossiers", exact: true });

    await expect(brainstormTab).toBeVisible({ timeout: 30_000 });

    await rndTab.click();
    await expect(
      page.getByPlaceholder(/Idée rapide/i)
    ).toBeVisible({ timeout: 15_000 });

    await dossiersTab.click();
    await expect(page.getByText(/Dossiers R&D/i)).toBeVisible({
      timeout: 15_000,
    });
  });
});

import { expect, test } from "@playwright/test";

test.describe("Briefing page", () => {
  test("renders briefing header", async ({ page }) => {
    await page.goto("/briefing");
    await expect(page.getByRole("heading", { name: /Briefing matinal/i })).toBeVisible({
      timeout: 30_000,
    });
  });

  test("shows COO tab when preview flag path used", async ({ page }) => {
    await page.goto("/briefing?preview=1");
    await expect(page.getByRole("button", { name: /Brief COO/i })).toBeVisible({
      timeout: 30_000,
    });
  });
});

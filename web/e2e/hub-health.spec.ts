import { expect, test } from "@playwright/test";

test.describe("Lobby", () => {
  test("loads without crash and shows ALNUA header", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Siège social")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText("ALNUA")).toBeVisible();
  });
});

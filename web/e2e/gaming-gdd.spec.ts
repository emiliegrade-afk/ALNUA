import { expect, test } from "@playwright/test";

test.describe("Gaming GDD workspace", () => {
  test("shows GDD Manager section with preview", async ({ page }) => {
    await page.goto("/gaming?preview=1");
    await expect(page.getByText("GDD Manager")).toBeVisible({ timeout: 30_000 });
  });
});

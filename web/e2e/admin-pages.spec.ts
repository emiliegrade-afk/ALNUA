import { expect, test } from "@playwright/test";

const adminPages = [
  { path: "/admin/costs", title: /Coûts LLM/i },
  { path: "/admin/events", title: /Event bus/i },
  { path: "/admin/ab-test", title: /A\/B test agents/i },
];

for (const { path, title } of adminPages) {
  test(`admin page ${path} loads with preview`, async ({ page }) => {
    const flagsDone = page.waitForResponse(
      (r) => r.url().includes("/admin/flags") && r.ok()
    );
    await page.goto(`${path}?preview=1`);
    await flagsDone;
    await expect(page.getByRole("heading", { name: title })).toBeVisible({
      timeout: 30_000,
    });
  });
}

test("admin hub lists tools when flags enabled", async ({ page }) => {
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: /Outils Tier 3/i })).toBeVisible({
    timeout: 30_000,
  });
});

import { expect, test } from "@playwright/test";

const ROUTES = [
  "/",
  "/briefing",
  "/secretary",
  "/ceo",
  "/hub",
  "/openroom",
  "/gaming",
  "/app",
  "/robo",
  "/finances",
  "/marketing",
  "/rd",
  "/academy",
  "/brand",
  "/analytics",
  "/connections",
  "/library",
  "/admin",
  "/admin/costs?preview=1",
  "/admin/events?preview=1",
  "/admin/ab-test?preview=1",
  "/beta",
  "/waitlist",
  "/releases",
  "/partnerships",
  "/partnerships/manage",
  "/settings",
  "/brainstorm",
  "/content",
  "/roadmap",
  "/tickets",
];

for (const path of ROUTES) {
  test(`page ${path} loads without crash`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    const response = await page.goto(path, { waitUntil: "domcontentloaded", timeout: 45_000 });
    expect(response?.status(), `${path} HTTP status`).toBeLessThan(500);

    await page.waitForTimeout(1500);

    const body = await page.locator("body").innerText();
    expect(body).not.toMatch(/Application error|Internal Server Error|ReferenceError|TypeError: Cannot/);

    const critical = errors.filter(
      (e) =>
        !e.includes("favicon") &&
        !e.includes("404") &&
        !e.includes("briefing/today") &&
        !e.includes("Hydration")
    );
    expect(critical, `JS errors on ${path}`).toEqual([]);
  });
}

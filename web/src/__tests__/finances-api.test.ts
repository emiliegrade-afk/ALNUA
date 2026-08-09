import { describe, expect, it } from "vitest";
import {
  currentMonthKey,
  formatCurrency,
  shiftMonth,
} from "@/lib/finances-api";

describe("finances-api helpers", () => {
  it("formats EUR in fr-FR", () => {
    const s = formatCurrency(12.5, "EUR");
    expect(s).toMatch(/12/);
    expect(s).toMatch(/€|EUR/);
  });

  it("currentMonthKey is YYYY-MM", () => {
    expect(currentMonthKey()).toMatch(/^\d{4}-\d{2}$/);
  });

  it("shiftMonth rolls across year boundary", () => {
    expect(shiftMonth("2026-01", -1)).toBe("2025-12");
    expect(shiftMonth("2025-12", 1)).toBe("2026-01");
  });
});

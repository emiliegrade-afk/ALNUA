import { describe, expect, it } from "vitest";
import { trustBand, trustBandLabel, trustPercent } from "@/lib/trust-api";

describe("trust-api helpers (DEC-011 bands)", () => {
  it("maps scores to autonomy bands", () => {
    expect(trustBand(0.69)).toBe("low");
    expect(trustBand(0.7)).toBe("review");
    expect(trustBand(0.9)).toBe("review");
    expect(trustBand(0.901)).toBe("autonomous");
  });

  it("formats percent and labels", () => {
    expect(trustPercent(0.734)).toBe(73);
    expect(trustBandLabel("low")).toMatch(/manager/i);
    expect(trustBandLabel("review")).toMatch(/Review Board/i);
    expect(trustBandLabel("autonomous")).toMatch(/Autonomie/i);
  });
});

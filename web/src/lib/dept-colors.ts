/** Unified ALNUA copper palette — single accent across all departments. */
const COPPER = {
  main: "#E09B6A",
  bg: "rgba(224, 155, 106, 0.10)",
  border: "rgba(224, 155, 106, 0.20)",
} as const;

const COPPER_LIGHT = {
  main: "#F0C4A0",
  bg: "rgba(217, 168, 143, 0.10)",
  border: "rgba(217, 168, 143, 0.20)",
} as const;

const COPPER_DIM = {
  main: "#B86E45",
  bg: "rgba(138, 96, 80, 0.10)",
  border: "rgba(138, 96, 80, 0.20)",
} as const;

export const DEPT_COLORS = {
  ceo: COPPER,
  secretary: COPPER,
  legal: COPPER,
  hub: COPPER,
  app: COPPER_LIGHT,
  gaming: COPPER,
  robo: COPPER,
  finances: COPPER,
  marketing: COPPER,
  rd: COPPER,
  brand: COPPER,
  analytics: COPPER,
  it: COPPER_DIM,
  academy: COPPER_LIGHT,
  lounge: COPPER_LIGHT,
  openroom: COPPER,
} as const;

export type DeptKey = keyof typeof DEPT_COLORS;

/** Active poles vs support services — left border opacity in lobby cards. */
export type DeptTier = "active" | "support";

export const DEPT_TIERS: Record<DeptKey, DeptTier> = {
  ceo: "active",
  secretary: "active",
  legal: "support",
  hub: "active",
  app: "active",
  gaming: "active",
  robo: "active",
  finances: "support",
  marketing: "support",
  rd: "support",
  brand: "support",
  analytics: "support",
  it: "support",
  academy: "active",
  lounge: "active",
  openroom: "active",
};

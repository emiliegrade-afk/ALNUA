/** Unified ALNUA copper palette — single accent across all departments. */
const COPPER = {
  main: "#C08A62",
  bg: "rgba(192, 138, 98, 0.10)",
  border: "rgba(192, 138, 98, 0.20)",
} as const;

const COPPER_LIGHT = {
  main: "#D4A882",
  bg: "rgba(212, 168, 130, 0.10)",
  border: "rgba(212, 168, 130, 0.20)",
} as const;

const COPPER_DIM = {
  main: "#7A5540",
  bg: "rgba(122, 85, 64, 0.10)",
  border: "rgba(122, 85, 64, 0.20)",
} as const;

export const DEPT_COLORS = {
  ceo: COPPER,
  secretary: COPPER,
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
} as const;

export type DeptKey = keyof typeof DEPT_COLORS;

/** Active poles vs support services — left border opacity in lobby cards. */
export type DeptTier = "active" | "support";

export const DEPT_TIERS: Record<DeptKey, DeptTier> = {
  ceo: "active",
  secretary: "active",
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
};

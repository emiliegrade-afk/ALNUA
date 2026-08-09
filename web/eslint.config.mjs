import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

/**
 * Flat config Next 16 (remplace .eslintrc + `next lint`).
 * Règles React Compiler / hooks v6 nouvelles volontairement off
 * (set-state-in-effect, purity, refs) — casseraient CI sur code préexistant.
 * À réactiver progressivement hors Vague 1.
 */
/** @type {import("eslint").Linter.Config[]} */
const eslintConfig = [
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/purity": "off",
      "react-hooks/refs": "off",
      "react-hooks/preserve-manual-memoization": "off",
    },
  },
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      ".next-build/**",
      "out/**",
      "build/**",
      "scripts/**",
      "next-env.d.ts",
    ],
  },
];

export default eslintConfig;

/**
 * Local production build that does not fight `next dev` over `.next/`.
 * Deploy/CI can keep using `next build` (default distDir `.next`) when no
 * concurrent dev server is writing the same cache.
 */
const { spawnSync } = require("child_process");
const path = require("path");

process.env.NEXT_DIST_DIR = process.env.NEXT_DIST_DIR || ".next-build";
process.env.NEXT_TELEMETRY_DISABLED = "1";

const webRoot = path.join(__dirname, "..");
const result = spawnSync("npx", ["next", "build"], {
  cwd: webRoot,
  stdio: "inherit",
  shell: true,
  env: process.env,
});

process.exit(result.status === null ? 1 : result.status);

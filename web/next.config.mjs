import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow an isolated production output dir when `next dev` holds `.next`.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  // Repo root has an empty package-lock for Hub scripts — pin tracing to web/.
  outputFileTracingRoot: path.join(__dirname),
  experimental: {
    optimizePackageImports: ["lucide-react", "date-fns", "recharts"],
  },
};

export default nextConfig;

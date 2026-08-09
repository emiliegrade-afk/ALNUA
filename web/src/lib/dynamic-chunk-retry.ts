import type { ComponentType } from "react";
import dynamic, { type DynamicOptionsLoadingProps } from "next/dynamic";

const CHUNK_RETRY_KEY = "alnua-chunk-retry";

function isChunkLoadError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  return (
    error.name === "ChunkLoadError" ||
    error.message.includes("Loading chunk") ||
    error.message.includes("Failed to fetch dynamically imported module")
  );
}

/** Retry dynamic import once; reload page if chunk hash is stale (dev rebuild). */
export function importWithChunkRetry<T>(
  loader: () => Promise<T>,
): Promise<T> {
  return loader().catch((error: unknown) => {
    if (
      typeof window !== "undefined" &&
      isChunkLoadError(error) &&
      !sessionStorage.getItem(CHUNK_RETRY_KEY)
    ) {
      sessionStorage.setItem(CHUNK_RETRY_KEY, "1");
      window.location.reload();
    }
    throw error;
  });
}

export function dynamicWithChunkRetry<P = Record<string, never>>(
  loader: () => Promise<{ default: ComponentType<P> }>,
  options?: {
    loading?: (props: DynamicOptionsLoadingProps) => React.ReactNode;
    ssr?: boolean;
  },
) {
  return dynamic(
    () => importWithChunkRetry(loader),
    { ssr: false, ...options },
  );
}

import type { ComponentType, ReactElement } from "react";
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

export function dynamicWithChunkRetry<P extends object = Record<string, never>>(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- next/dynamic + named exports infer `never` props
  loader: () => Promise<{ default: ComponentType<any> }>,
  options?: {
    loading?: (props: DynamicOptionsLoadingProps) => ReactElement | null;
    ssr?: boolean;
  },
) {
  return dynamic<P>(
    () => importWithChunkRetry(loader) as Promise<{ default: ComponentType<P> }>,
    { ssr: false, ...options },
  );
}

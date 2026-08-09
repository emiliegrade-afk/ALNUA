"use client";

import { useEffect, useState } from "react";
import { brandAssetUrl } from "@/lib/brand-api";
import { hubApiKeyHeaders } from "@/lib/hub-api-key";
import { cn } from "@/lib/utils";

interface BrandAssetImageProps {
  filePath: string;
  alt: string;
  className?: string;
  draggable?: boolean;
}

/** Loads brand assets with X-Hub-Key (img src cannot send custom headers). */
export function BrandAssetImage({
  filePath,
  alt,
  className,
  draggable = false,
}: BrandAssetImageProps) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;

    async function load() {
      try {
        const res = await fetch(brandAssetUrl(filePath), {
          cache: "no-store",
          headers: hubApiKeyHeaders(),
        });
        if (!res.ok || cancelled) return;
        const blob = await res.blob();
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      } catch {
        if (!cancelled) setSrc(null);
      }
    }

    void load();
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [filePath]);

  if (!src) {
    return (
      <div
        className={cn("animate-pulse rounded bg-obsidian/50", className)}
        aria-hidden
      />
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      className={className}
      draggable={draggable}
    />
  );
}

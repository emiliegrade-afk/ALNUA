"use client";

import type { RndIdea } from "@/lib/rnd";
import { RndPitchModal } from "@/components/rnd/rnd-pitch-modal";

/** @deprecated Use RndPitchModal directly — kept as alias for existing imports. */
export function RndIdeaDetailModal({
  idea,
  open,
  onOpenChange,
  onPromoted,
  onRefresh,
}: {
  idea: RndIdea | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPromoted?: (dossierId: string) => void;
  onRefresh?: () => void;
}) {
  return (
    <RndPitchModal
      idea={idea}
      open={open}
      onOpenChange={onOpenChange}
      onPromoted={onPromoted}
      onRefresh={onRefresh}
    />
  );
}

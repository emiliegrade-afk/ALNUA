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
  onArchive,
}: {
  idea: RndIdea | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPromoted?: (dossierId: string) => void;
  onRefresh?: () => void;
  onArchive?: (idea: RndIdea) => void | Promise<void>;
}) {
  return (
    <RndPitchModal
      idea={idea}
      open={open}
      onOpenChange={onOpenChange}
      onPromoted={onPromoted}
      onRefresh={onRefresh}
      onArchive={onArchive}
    />
  );
}

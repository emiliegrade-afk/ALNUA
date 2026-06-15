import { Suspense } from "react";
import { RdPageContent } from "./rd-page-content";

export default function RdPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-48 items-center justify-center text-sm text-titanium/60">
          Chargement R&D…
        </div>
      }
    >
      <RdPageContent />
    </Suspense>
  );
}

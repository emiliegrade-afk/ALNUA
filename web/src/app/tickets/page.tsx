import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import { TicketsView } from "@/components/tickets/tickets-view";

export default function TicketsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-20 text-titanium">
          <Loader2 className="mr-2 h-5 w-5 animate-spin text-copper" />
          Chargement…
        </div>
      }
    >
      <TicketsView />
    </Suspense>
  );
}

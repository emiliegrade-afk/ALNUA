import { AdminEventsView } from "@/components/admin/events/admin-events-view";
import { AdminGate } from "@/components/admin/admin-gate";
import { AdminShell } from "@/components/admin/admin-shell";

export default function AdminEventsPage() {
  return (
    <AdminGate page="events" title="Event bus">
      <AdminShell
        title="Event bus"
        subtitle="Pub/sub inter-agents — timeline et stats en mémoire"
      >
        <AdminEventsView />
      </AdminShell>
    </AdminGate>
  );
}

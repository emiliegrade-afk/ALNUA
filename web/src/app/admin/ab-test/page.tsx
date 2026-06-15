import { AdminAbTestView } from "@/components/admin/ab-test/admin-ab-test-view";
import { AdminGate } from "@/components/admin/admin-gate";
import { AdminShell } from "@/components/admin/admin-shell";

export default function AdminAbTestPage() {
  return (
    <AdminGate page="ab-test" title="A/B test">
      <AdminShell
        title="A/B test agents"
        subtitle="Alex (QA) juge · quick-compare sur deux variants de kwargs"
      >
        <AdminAbTestView />
      </AdminShell>
    </AdminGate>
  );
}

import { BrainstormView } from "@/components/brainstorm/brainstorm-view";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";

export default function RdPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="rd"
        title="R&D"
        subtitle="Brainstorm · Idées · Sessions · Mémoire"
      />
      <div className="-mx-6 flex h-[calc(100dvh-12rem)] flex-col overflow-hidden">
        <BrainstormView />
      </div>
    </>
  );
}

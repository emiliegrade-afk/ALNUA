import { AcademyCockpit } from "@/components/hub/academy-cockpit";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";

export default function AcademyPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="academy"
        title="ALNUA Academy"
        subtitle="Salle d'entraînement · Niveaux · Sprints · Validation agents"
      />
      <AcademyCockpit />
    </>
  );
}

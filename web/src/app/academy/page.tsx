import { AcademyCockpit } from "@/components/hub/academy-cockpit";
import { BureauLibraryPopup } from "@/components/library/bureau-library-popup";
import { BureauPage } from "@/components/shared/bureau-page";
import Link from "next/link";

export default function AcademyPage() {
  return (
    <BureauPage
      dept="academy"
      title="ALNUA Academy"
      subtitle="Salle d'entraînement · Niveaux · Sprints · Validation agents"
    >
      <p className="rounded-xl border border-bronze-faint bg-obsidian/70 px-4 py-3 font-body text-sm text-titane/80">
        <Link href="/ide" className="text-bronze-bright underline-offset-2 hover:underline">
          Ouvrir l&apos;IDE Hub
        </Link>
        {" "}
        — code, observe les agents, apprends avec Luca.
      </p>
      <AcademyCockpit />
      <BureauLibraryPopup bureau="academy" />
    </BureauPage>
  );
}

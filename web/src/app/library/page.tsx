import { BureauPage } from "@/components/shared/bureau-page";
import {
  BureauLibraryPanel,
  LibraryCeoReportCard,
  LibraryTeamEnrichCard,
} from "@/components/library/bureau-library-panel";
import { LibraryDistributionCard } from "@/components/library/library-distribution-card";
import { LibraryHubManualCard } from "@/components/library/library-hub-manual-card";
import { LibraryRetentionCard } from "@/components/library/library-retention-card";

export default function LibraryPage() {
  return (
    <BureauPage
      dept="hub"
      title="Bibliothèque ALNUA"
      subtitle="Recherche · archives par bureau · tout est conservé"
    >
      <LibraryHubManualCard />
      <LibraryDistributionCard />
      <LibraryRetentionCard />
      <BureauLibraryPanel showResearch />
      <LibraryTeamEnrichCard />
      <LibraryCeoReportCard />
    </BureauPage>
  );
}

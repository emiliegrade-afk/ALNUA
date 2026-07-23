import { BrandView } from "@/components/brand/brand-view";
import { BureauPage } from "@/components/shared/bureau-page";

export default function BrandPage() {
  return (
    <BureauPage
      dept="brand"
      title="Direction Artistique"
      subtitle="Brand Kit · Assets · Charte graphique"
    >
      <BrandView />
    </BureauPage>
  );
}

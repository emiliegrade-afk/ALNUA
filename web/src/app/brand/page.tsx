import { BrandView } from "@/components/brand/brand-view";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";

export default function BrandPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="brand"
        title="Direction Artistique"
        subtitle="Brand Kit · Assets · Charte graphique"
      />
      <BrandView />
    </>
  );
}

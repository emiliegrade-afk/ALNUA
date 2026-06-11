import { BetaPublicPortal } from "@/components/beta/beta-public-portal";

interface BetaPublicPageProps {
  params: { project_slug: string };
}

export default function BetaPublicPage({ params }: BetaPublicPageProps) {
  return <BetaPublicPortal projectSlug={params.project_slug} />;
}

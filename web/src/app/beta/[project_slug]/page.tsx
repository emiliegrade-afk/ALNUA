import { BetaPublicPortal } from "@/components/beta/beta-public-portal";

interface BetaPublicPageProps {
  params: Promise<{ project_slug: string }>;
}

export default async function BetaPublicPage({ params }: BetaPublicPageProps) {
  const { project_slug } = await params;
  return <BetaPublicPortal projectSlug={project_slug} />;
}

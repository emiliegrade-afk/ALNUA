import { WaitlistPublicPortal } from "@/components/waitlist/waitlist-public-portal";

interface WaitlistPublicPageProps {
  params: Promise<{ project_slug: string }>;
}

export default async function WaitlistPublicPage({ params }: WaitlistPublicPageProps) {
  const { project_slug } = await params;
  return <WaitlistPublicPortal projectSlug={project_slug} />;
}

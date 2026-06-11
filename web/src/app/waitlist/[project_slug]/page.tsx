import { WaitlistPublicPortal } from "@/components/waitlist/waitlist-public-portal";

interface WaitlistPublicPageProps {
  params: { project_slug: string };
}

export default function WaitlistPublicPage({ params }: WaitlistPublicPageProps) {
  return <WaitlistPublicPortal projectSlug={params.project_slug} />;
}

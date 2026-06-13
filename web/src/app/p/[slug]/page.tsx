import type { Metadata } from "next";
import { hubBackendBaseUrl } from "@/lib/hub-api-config";
import { RndProductPublicPage } from "@/components/product/rnd-product-public-page";

interface ProductPublicPageProps {
  params: { slug: string };
}

async function fetchProductMeta(slug: string): Promise<{
  title?: string;
  tagline?: string;
  seo_title?: string;
  seo_description?: string;
} | null> {
  const base = hubBackendBaseUrl();
  const key =
    process.env.HUB_API_KEY?.trim() ||
    process.env.NEXT_PUBLIC_HUB_API_KEY?.trim() ||
    "";
  try {
    const res = await fetch(`${base}/rnd/product/${encodeURIComponent(slug)}`, {
      headers: key ? { "X-Hub-Key": key } : {},
      next: { revalidate: 120 },
    });
    if (!res.ok) return null;
    return res.json() as Promise<{
      title?: string;
      tagline?: string;
      seo_title?: string;
      seo_description?: string;
    }>;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: ProductPublicPageProps): Promise<Metadata> {
  const page = await fetchProductMeta(params.slug);
  if (!page) {
    return { title: "Produit — ALNUA" };
  }
  return {
    title: page.seo_title ?? `${page.title} — ALNUA`,
    description: page.seo_description ?? page.tagline ?? undefined,
    openGraph: {
      title: page.seo_title ?? page.title,
      description: page.seo_description ?? page.tagline ?? undefined,
    },
  };
}

export default function ProductPublicPage({ params }: ProductPublicPageProps) {
  return <RndProductPublicPage slug={params.slug} />;
}

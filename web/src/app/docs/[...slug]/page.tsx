import Link from "next/link";
import { notFound } from "next/navigation";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { readHubDoc, rewriteDocMarkdownLinks } from "@/lib/docs-fs";
import { ROUTES } from "@/lib/routes";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ slug: string[] }>;
};

export default async function HubDocPage({ params }: PageProps) {
  const { slug } = await params;
  const doc = readHubDoc(slug);
  if (!doc) notFound();

  const body = rewriteDocMarkdownLinks(doc.markdown, doc.relPath);
  const title =
    body.match(/^#\s+(.+)$/m)?.[1]?.trim() ??
    slug[slug.length - 1]?.replace(/-/g, " ") ??
    "Document";

  return (
    <div className="min-h-screen bg-obsidian px-4 py-8 text-ivory sm:px-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex flex-wrap items-center gap-3 text-xs uppercase tracking-widest text-copper">
          <Link
            href={ROUTES.docs}
            className="inline-flex items-center gap-2 transition hover:text-copper-light"
          >
            <AlnuaStar size={18} animated={false} />
            Documents
          </Link>
          <span className="text-titanium/40">/</span>
          <Link href={ROUTES.userManual} className="transition hover:text-copper-light">
            Manuel
          </Link>
          <span className="text-titanium/40">·</span>
          <Link href={ROUTES.ceo} className="text-titanium/70 transition hover:text-copper-light">
            Bureau du CEO
          </Link>
        </div>

        <p className="font-body text-[11px] text-titanium/50">docs/{doc.relPath}</p>
        <h1 className="mt-2 font-title text-2xl font-medium tracking-wide text-ivory sm:text-3xl">
          {title}
        </h1>

        <div className="mt-8 rounded-xl border border-copper/15 bg-obsidian/60 p-5 sm:p-8">
          <MarkdownContent>{body.replace(/^#\s+.+\n+/, "")}</MarkdownContent>
        </div>
      </div>
    </div>
  );
}

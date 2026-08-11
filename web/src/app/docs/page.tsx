import Link from "next/link";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { ROUTES } from "@/lib/routes";

type GuideLink = { href: string; title: string; desc: string };
type GuideDoc = { title: string; file: string; desc?: string };

const GUIDES: (GuideLink | GuideDoc)[] = [
  { href: ROUTES.ceo, title: "Bureau CEO", desc: "Cockpit — manuel en tête de page + décisions" },
  {
    title: "Manuel utilisateur (noob)",
    file: "guides/user-manual.md",
    desc: "Mode d'emploi complet — lisible dans le Hub",
  },
  { title: "Templates contrats", file: "guides/contract-templates-catalog.md" },
  { title: "First 15 minutes", file: "getting-started/first-15-minutes.md" },
  { title: "Installation", file: "getting-started/installation.md" },
  { title: "Concepts", file: "getting-started/concepts.md" },
  { title: "Content pipeline", file: "guides/use-case-content-creation.md" },
  { title: "R&D pipeline", file: "guides/use-case-r-d-pipeline.md" },
  { title: "Coding pipeline", file: "guides/use-case-coding-pipeline.md" },
  { title: "Sécurité Hub", file: "guides/SECURITY_HARDENING.md" },
  { title: "Authentication", file: "api/authentication.md" },
];

function isGuideLink(g: GuideLink | GuideDoc): g is GuideLink {
  return "href" in g;
}

function docHref(file: string): string {
  return `/docs/${file.replace(/\.md$/i, "")}`;
}

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-obsidian p-8 text-ivory">
      <div className="mx-auto max-w-2xl">
        <Link
          href="/landing"
          className="inline-flex items-center gap-2 font-body text-xs uppercase tracking-widest text-copper transition hover:text-copper-light"
        >
          <AlnuaStar size={18} animated={false} />
          ALNUA Hub
        </Link>

        <h1 className="mt-6 font-title text-3xl font-medium tracking-[0.2em] text-ivory">
          Documentation
        </h1>
        <p className="mt-2 font-body text-sm text-titanium">
          Guides du repo, lisibles ici — commence par le{" "}
          <Link href={ROUTES.userManual} className="text-copper hover:text-copper-light">
            manuel utilisateur
          </Link>
          .
        </p>

        <ul className="mt-10 space-y-3">
          {GUIDES.map((g) => {
            const href = isGuideLink(g) ? g.href : docHref(g.file);
            const subtitle = isGuideLink(g)
              ? g.desc
              : g.desc ?? `docs/${g.file}`;
            return (
              <li
                key={g.title}
                className="rounded-lg border border-copper/15 bg-obsidian/60 p-4 transition-colors hover:border-copper/30"
              >
                <Link
                  href={href}
                  className="font-title text-sm tracking-wide text-copper-light transition hover:text-copper"
                >
                  {g.title}
                </Link>
                <p className="mt-1 font-body text-xs text-titanium/70">{subtitle}</p>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

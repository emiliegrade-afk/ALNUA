import Link from "next/link";



type GuideLink = { href: string; title: string; desc: string };

type GuideDoc = { title: string; file: string };



const GUIDES: (GuideLink | GuideDoc)[] = [

  { href: "/ceo", title: "Ouvrir le Hub", desc: "Cockpit CEO — assistants, briefing, ops" },

  { title: "First 15 minutes", file: "getting-started/first-15-minutes.md" },

  { title: "Installation", file: "getting-started/installation.md" },

  { title: "Concepts", file: "getting-started/concepts.md" },

  { title: "Content pipeline", file: "guides/use-case-content-creation.md" },

  { title: "R&D pipeline", file: "guides/use-case-r-d-pipeline.md" },

  { title: "Coding pipeline", file: "guides/use-case-coding-pipeline.md" },

  { title: "Authentication", file: "api/authentication.md" },

];



function isGuideLink(g: GuideLink | GuideDoc): g is GuideLink {

  return "href" in g;

}



export default function DocsPage() {

  return (

    <div className="min-h-screen bg-[#0a0a0f] p-8 text-ivory">

      <div className="mx-auto max-w-2xl">

        <Link href="/landing" className="text-sm text-copper hover:underline">

          ← ALNUA Hub

        </Link>

        <h1 className="mt-4 font-display text-3xl font-bold">Documentation</h1>

        <p className="mt-2 text-titanium">

          Guides dans <code className="text-copper">docs/</code> du repo.

        </p>

        <ul className="mt-8 space-y-3">

          {GUIDES.map((g) => (

            <li

              key={g.title}

              className="rounded-lg border border-white/[0.08] p-4"

            >

              {isGuideLink(g) ? (

                <Link href={g.href} className="font-medium text-copper-glow hover:underline">

                  {g.title}

                </Link>

              ) : (

                <span className="font-medium">{g.title}</span>

              )}

              <p className="mt-1 text-sm text-titanium">

                {isGuideLink(g) ? g.desc : `docs/${g.file}`}

              </p>

            </li>

          ))}

        </ul>

      </div>

    </div>

  );

}


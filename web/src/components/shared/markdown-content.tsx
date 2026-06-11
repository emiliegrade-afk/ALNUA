"use client";

import dynamic from "next/dynamic";

const ReactMarkdown = dynamic(() => import("react-markdown"), {
  ssr: false,
  loading: () => (
    <p className="text-sm italic text-titanium/60">Chargement…</p>
  ),
});

interface MarkdownContentProps {
  children: string;
  className?: string;
}

export function MarkdownContent({ children, className }: MarkdownContentProps) {
  if (!children.trim()) {
    return (
      <p className="text-sm italic text-titanium/60">Aucun contenu</p>
    );
  }

  return (
    <article
      className={
        className ??
        "prose prose-invert prose-sm max-w-none prose-headings:text-ivory prose-p:text-titanium prose-li:text-titanium prose-strong:text-ivory prose-hr:border-white/10"
      }
    >
      <ReactMarkdown>{children}</ReactMarkdown>
    </article>
  );
}

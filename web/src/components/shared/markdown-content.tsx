"use client";

import ReactMarkdown from "react-markdown";

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
        "prose prose-invert prose-sm max-w-none prose-headings:text-ivory prose-p:text-titanium prose-li:text-titanium prose-strong:text-ivory prose-hr:border-copper/15"
      }
    >
      <ReactMarkdown>{children}</ReactMarkdown>
    </article>
  );
}

/**
 * Read Hub docs/*.md from the repo (sibling of web/) for in-app rendering.
 * Path traversal is rejected — only files under docs/ are allowed.
 */
import { existsSync, readFileSync } from "fs";
import { join, normalize, relative, resolve, sep, dirname } from "path";

export function hubDocsRoot(): string {
  return resolve(process.cwd(), "..", "docs");
}

/** Slug segments → absolute path under docs/, or null if unsafe / missing. */
export function resolveHubDocPath(slug: string[]): string | null {
  if (!slug.length) return null;
  const cleaned = slug.map((s) => s.replace(/\.md$/i, "")).filter(Boolean);
  if (!cleaned.length) return null;
  if (cleaned.some((s) => s.includes("..") || s.includes(sep) || s.includes("/") || s.includes("\\"))) {
    return null;
  }
  const root = hubDocsRoot();
  const candidate = normalize(join(root, ...cleaned) + ".md");
  const rel = relative(root, candidate);
  if (!rel || rel.startsWith("..") || rel.includes(`..${sep}`)) return null;
  if (!existsSync(candidate)) return null;
  return candidate;
}

export function readHubDoc(slug: string[]): { markdown: string; relPath: string } | null {
  const abs = resolveHubDocPath(slug);
  if (!abs) return null;
  const root = hubDocsRoot();
  const relPath = relative(root, abs).split(sep).join("/");
  const markdown = readFileSync(abs, "utf8").replace(/^\uFEFF/, "");
  return { markdown, relPath };
}

/**
 * Rewrite relative *.md links so they open inside /docs/... in the Hub.
 * fromRelPath = e.g. "guides/user-manual.md"
 */
export function rewriteDocMarkdownLinks(markdown: string, fromRelPath: string): string {
  const fromDir = dirname(fromRelPath).split(sep).join("/");
  return markdown.replace(
    /\]\((?!https?:\/\/|\/|#|mailto:)([^)]+\.md)(#[^)]*)?\)/gi,
    (_full, target: string, hash: string = "") => {
      const joined = join(fromDir === "." ? "" : fromDir, target)
        .split(sep)
        .join("/");
      const normalized = joined
        .split("/")
        .filter((p) => p && p !== ".")
        .reduce<string[]>((acc, part) => {
          if (part === "..") {
            acc.pop();
          } else {
            acc.push(part);
          }
          return acc;
        }, []);
      const withoutMd = normalized.join("/").replace(/\.md$/i, "");
      return `](/docs/${withoutMd}${hash || ""})`;
    },
  );
}

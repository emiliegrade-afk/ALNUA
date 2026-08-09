/** Shared department routes for prototype shell ↔ Hub pages. */
export type ProtoDeptName =
  | "Direction"
  | "Secrétariat"
  | "CEO"
  | "R&D"
  | "APP"
  | "Gaming"
  | "Robotique"
  | "Marketing"
  | "Comptabilité"
  | "Analytics"
  | "Brand Design";

export const PROTO_DEPT_HREF: Record<ProtoDeptName, string> = {
  Direction: "/hub",
  Secrétariat: "/secretary",
  CEO: "/ceo",
  "R&D": "/rd",
  APP: "/app",
  Gaming: "/gaming",
  Robotique: "/robo",
  Marketing: "/marketing",
  Comptabilité: "/finances",
  Analytics: "/analytics",
  "Brand Design": "/brand",
};

export const PROTO_PATH_TO_DEPT: Record<string, ProtoDeptName> = {
  "/hub": "Direction",
  "/secretary": "Secrétariat",
  "/ceo": "CEO",
  "/rd": "R&D",
  "/app": "APP",
  "/gaming": "Gaming",
  "/robo": "Robotique",
  "/marketing": "Marketing",
  "/finances": "Comptabilité",
  "/analytics": "Analytics",
  "/brand": "Brand Design",
};

/** All Hub paths that use the prototype AGENTIC OS shell (no MockupShell). */
export const PROTO_SHELL_PATHS = Object.values(PROTO_DEPT_HREF);

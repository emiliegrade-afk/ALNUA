/** Navigation détail projet — retour vers le bureau d'origine. */

const BACK_ROUTE_BY_BRANCH: Record<string, string> = {
  app: "/app",
  gaming: "/gaming",
  robotics: "/robo",
  other: "/app",
};

export function backRouteFor(branch: string): string {
  return BACK_ROUTE_BY_BRANCH[branch] ?? "/app";
}

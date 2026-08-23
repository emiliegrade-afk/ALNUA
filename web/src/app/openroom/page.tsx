import { redirect } from "next/navigation";

type Props = {
  searchParams: Promise<{ agent?: string | string[] }>;
};

/** Legacy OpenRoom URL → Agent Lounge (DEC-031). */
export default async function OpenRoomRedirectPage({ searchParams }: Props) {
  const sp = await searchParams;
  const raw = sp.agent;
  const agent = Array.isArray(raw) ? raw[0] : raw;
  const q =
    typeof agent === "string" && agent.length > 0
      ? `?agent=${encodeURIComponent(agent)}`
      : "";
  redirect(`/lounge${q}`);
}

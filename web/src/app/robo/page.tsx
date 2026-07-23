"use client";

import dynamic from "next/dynamic";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { BureauPage } from "@/components/shared/bureau-page";

const RoboConsole = dynamic(
  () =>
    import("@/components/robo/robo-console").then((m) => ({
      default: m.RoboConsole,
    })),
  {
    loading: () => (
      <p className="text-sm text-titane/60">Chargement console robotique…</p>
    ),
  },
);

export default function RoboPage() {
  return (
    <BureauPage
      dept="robo"
      title="Pôle Robotique"
      subtitle="Eve Robot · Raspberry Pi · Hardware"
    >
      <BureauAgentsSection bureau="robo" />
      <RoboConsole />
    </BureauPage>
  );
}

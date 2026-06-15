"use client";

import dynamic from "next/dynamic";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";

const RoboConsole = dynamic(
  () =>
    import("@/components/robo/robo-console").then((m) => ({
      default: m.RoboConsole,
    })),
  {
    loading: () => (
      <p className="text-sm text-titanium/60">Chargement console robotique…</p>
    ),
  }
);

export default function RoboPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="robo"
        title="Pôle Robotique"
        subtitle="Eve Robot · Raspberry Pi · Hardware"
      />

      <BureauAgentsSection bureau="robo" />

      <RoboConsole />
    </>
  );
}

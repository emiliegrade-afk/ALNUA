"use client";

import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { RoboConsole } from "@/components/robo/robo-console";

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

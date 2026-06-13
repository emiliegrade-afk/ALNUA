"use client";

import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { ModelSettingsView } from "@/components/settings/model-settings-view";

export default function SettingsPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="hub"
        title="Paramètres"
        subtitle="Modèles LLM · Configuration agents"
      />
      <div className="mt-6">
        <ModelSettingsView />
      </div>
    </>
  );
}

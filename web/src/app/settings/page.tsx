"use client";

import { BureauPage } from "@/components/shared/bureau-page";
import { ModelSettingsView } from "@/components/settings/model-settings-view";

export default function SettingsPage() {
  return (
    <BureauPage
      dept="hub"
      title="Paramètres"
      subtitle="Modèles LLM · Configuration agents"
    >
      <ModelSettingsView />
    </BureauPage>
  );
}

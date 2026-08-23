"use client";

import { BureauPage } from "@/components/shared/bureau-page";
import { ConnectivitySettings } from "@/components/settings/connectivity-settings";
import { ModelSettingsView } from "@/components/settings/model-settings-view";

export default function SettingsPage() {
  return (
    <BureauPage
      dept="hub"
      title="Paramètres"
      subtitle="Modèles LLM · Configuration agents"
    >
      <div className="space-y-6">
        <ConnectivitySettings />
        <ModelSettingsView />
      </div>
    </BureauPage>
  );
}

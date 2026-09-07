"use client";

import { C } from "../app-v2/shared";

/* Onglet placeholder honnête — sections sans source de données (ex. SEO).
   Libellé « non branché » plutôt que « coming soon » trompeur. */

export function ComingSoonTab({ title, reason }: { title: string; reason: string }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-3 rounded-2xl border p-10 text-center" style={{ borderColor: C.line, background: "rgba(19,19,22,.5)" }}>
      <span className="flex h-12 w-12 items-center justify-center rounded-full border text-[18px]" style={{ borderColor: "rgba(224,155,106,.35)", color: C.copperLight }}>
        ⏳
      </span>
      <h3 className="text-[15px] font-semibold" style={{ color: C.ivory }}>
        {title} — non branché
      </h3>
      <p className="max-w-md text-[11.5px] leading-relaxed" style={{ color: C.muted }}>
        {reason}
      </p>
    </div>
  );
}

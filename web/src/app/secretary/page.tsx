"use client";

import Link from "next/link";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { SecretaryConsole } from "@/components/secretary/secretary-console";
import { Button } from "@/components/ui/button";

export default function SecretaryPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="secretary"
        title="Secrétariat de Direction"
        subtitle="Nadia Faure · Emails · Agenda · Contrats · Réunions"
        breadcrumb="Secrétariat"
      />

      <BureauAgentsSection bureau="secretary" className="mb-8 grid gap-4 sm:grid-cols-1" />

      <SecretaryConsole />

      <div className="mt-8 flex flex-wrap gap-3">
        <Button asChild variant="outline" className="border-copper/30 hover:border-copper/50">
          <Link href="/ceo">Bureau du CEO</Link>
        </Button>
        <Button asChild variant="outline" className="border-copper/30 hover:border-copper/50">
          <Link href="/hub">Direction — COO</Link>
        </Button>
      </div>
    </>
  );
}

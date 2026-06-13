"use client";

import Link from "next/link";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCooStore } from "@/store/coo-store";

export default function SecretaryPage() {
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
  const openDrawer = useCooStore((s) => s.openDrawer);

  function delegate(task: string) {
    setPrefillMessage(task);
    openDrawer();
  }

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

      <section>
        <h2 className="label-caps mb-4">Actions rapides</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Card className="border-copper/20 bg-obsidian-2/90">
            <CardHeader className="pb-2">
              <CardTitle className="font-title text-base text-ivory">
                Emails & triage
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                className="border-copper/30 hover:border-copper/50"
                onClick={() => delegate("Nadia, trie mes emails prioritaires du jour")}
              >
                Trier les emails
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-copper/30 hover:border-copper/50"
                onClick={() => delegate("Nadia, rédige un email professionnel pour : ")}
              >
                Rédiger un email
              </Button>
            </CardContent>
          </Card>

          <Card className="border-copper/20 bg-obsidian-2/90">
            <CardHeader className="pb-2">
              <CardTitle className="font-title text-base text-ivory">
                Réunions & contrats
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                className="border-copper/30 hover:border-copper/50"
                onClick={() => delegate("Nadia, planifie une réunion avec l'ordre du jour suivant : ")}
              >
                Planifier une réunion
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-copper/30 hover:border-copper/50"
                onClick={() => delegate("Nadia, prépare un brouillon de contrat pour : ")}
              >
                Brouillon contrat
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="mt-4 flex flex-wrap gap-3">
          <Button asChild variant="outline" className="border-copper/30 hover:border-copper/50">
            <Link href="/ceo">Bureau du CEO</Link>
          </Button>
          <Button asChild variant="outline" className="border-copper/30 hover:border-copper/50">
            <Link href="/hub">Direction — COO</Link>
          </Button>
        </div>
      </section>
    </>
  );
}

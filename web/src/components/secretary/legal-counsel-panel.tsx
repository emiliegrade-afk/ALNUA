"use client";

import { useCallback, useState } from "react";
import { FileText, Loader2, Scale } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  legalAdvise,
  legalReview,
  listLegalTemplates,
  type ContractTemplate,
} from "@/lib/legal-counsel-api";
import { toast } from "sonner";

export function LegalCounselPanel() {
  const [templates, setTemplates] = useState<ContractTemplate[] | null>(null);
  const [question, setQuestion] = useState("");
  const [doc, setDoc] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadTemplates = useCallback(async () => {
    try {
      const res = await listLegalTemplates();
      setTemplates(res.templates);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Templates injoignables");
    }
  }, []);

  async function ask() {
    if (!question.trim()) return;
    setBusy(true);
    setAnswer(null);
    try {
      const res = await legalAdvise({ question: question.trim() });
      const text =
        (typeof res.advice === "string" && res.advice) ||
        (typeof res.summary === "string" && res.summary) ||
        JSON.stringify(res, null, 2);
      setAnswer(text);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Avis impossible");
    } finally {
      setBusy(false);
    }
  }

  async function review() {
    if (!doc.trim()) return;
    setBusy(true);
    setAnswer(null);
    try {
      const res = await legalReview({ document_text: doc.trim() });
      const text =
        (typeof res.review === "string" && res.review) ||
        (typeof res.summary === "string" && res.summary) ||
        JSON.stringify(res, null, 2);
      setAnswer(text);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Review impossible");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="border-copper/30 bg-obsidian-2/90">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
          <Scale className="h-4 w-4 text-copper" />
          Solène — Avocate d&apos;entreprise
        </CardTitle>
        <p className="label-caps">UE · USA · Asie · aide à la décision, pas barreau</p>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => void loadTemplates()}>
            <FileText className="mr-1 h-3.5 w-3.5" />
            Templates
          </Button>
        </div>
        {templates && (
          <ul className="space-y-1 text-xs text-titanium/80">
            {templates.map((t) => (
              <li key={t.id}>
                <span className="text-ivory">{t.label}</span>{" "}
                <span className="text-titanium/50">({t.jurisdictions.join(", ")})</span>
              </li>
            ))}
          </ul>
        )}
        <textarea
          className="min-h-[72px] w-full rounded border border-copper/20 bg-obsidian-1 px-3 py-2 text-sm text-ivory"
          placeholder="Question juridique…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <Button type="button" size="sm" disabled={busy} onClick={() => void ask()}>
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Demander un avis"}
        </Button>
        <textarea
          className="min-h-[100px] w-full rounded border border-copper/20 bg-obsidian-1 px-3 py-2 text-sm text-ivory"
          placeholder="Coller un contrat à faire relire…"
          value={doc}
          onChange={(e) => setDoc(e.target.value)}
        />
        <Button type="button" size="sm" variant="secondary" disabled={busy} onClick={() => void review()}>
          Faire relire avant signature
        </Button>
        {answer && (
          <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded bg-obsidian-1 p-3 text-xs text-ivory/90">
            {answer}
          </pre>
        )}
      </CardContent>
    </Card>
  );
}

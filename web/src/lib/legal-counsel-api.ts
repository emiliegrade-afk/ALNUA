import { hubFetch } from "./hub-fetch";

export type ContractTemplate = {
  id: string;
  label: string;
  jurisdictions: string[];
  article_titles: string[];
  has_body?: boolean;
};

export function listLegalTemplates(): Promise<{ templates: ContractTemplate[] }> {
  return hubFetch("/agents/legal-counsel/templates");
}

export function legalAdvise(body: {
  question: string;
  regions?: string[];
  context?: string;
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/legal-counsel/advise", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

export function legalReview(body: {
  document_text: string;
  doc_kind?: string;
  regions?: string[];
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/legal-counsel/review", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

export function legalValidateBeforeSign(body: {
  document_text: string;
  regions?: string[];
}): Promise<Record<string, unknown>> {
  return hubFetch("/agents/legal-counsel/validate-before-sign", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

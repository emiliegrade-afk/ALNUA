"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface AgentFormField {
  name: string;
  label: string;
  type?: "text" | "textarea" | "select" | "number";
  placeholder?: string;
  required?: boolean;
  defaultValue?: string;
  options?: Array<{ value: string; label: string }>;
  rows?: number;
}

interface AgentActionConsoleProps {
  title: string;
  description?: string;
  fields: AgentFormField[];
  submitLabel?: string;
  onSubmit: (values: Record<string, string>) => Promise<unknown>;
  className?: string;
}

function formatResult(data: unknown): string {
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if (typeof obj.result === "string") return obj.result;
    return JSON.stringify(data, null, 2);
  }
  return String(data);
}

export function AgentActionConsole({
  title,
  description,
  fields,
  submitLabel = "Exécuter",
  onSubmit,
  className,
}: AgentActionConsoleProps) {
  const [values, setValues] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {};
    for (const f of fields) {
      if (f.defaultValue) init[f.name] = f.defaultValue;
    }
    return init;
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    for (const f of fields) {
      if (f.required && !values[f.name]?.trim()) {
        toast.error(`${f.label} est requis`);
        return;
      }
    }
    setLoading(true);
    setResult(null);
    try {
      const data = await onSubmit(values);
      setResult(formatResult(data));
      toast.success("Terminé");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className={`border-copper/20 bg-obsidian-2/90 ${className ?? ""}`}>
      <CardHeader className="pb-2">
        <CardTitle className="font-title text-base text-ivory">{title}</CardTitle>
        {description ? (
          <p className="font-body text-xs text-titanium/60">{description}</p>
        ) : null}
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          {fields.map((field) => (
            <div key={field.name} className="space-y-1">
              <label className="label-caps text-[10px]">{field.label}</label>
              {field.type === "textarea" ? (
                <Textarea
                  value={values[field.name] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [field.name]: e.target.value }))
                  }
                  placeholder={field.placeholder}
                  rows={field.rows ?? 3}
                  className="border-copper/15 bg-white/[0.02] text-ivory/90"
                />
              ) : field.type === "select" && field.options ? (
                <Select
                  value={values[field.name] ?? field.defaultValue ?? ""}
                  onValueChange={(v) =>
                    setValues((prev) => ({ ...prev, [field.name]: v }))
                  }
                >
                  <SelectTrigger className="border-copper/15 bg-white/[0.02]">
                    <SelectValue placeholder={field.placeholder} />
                  </SelectTrigger>
                  <SelectContent>
                    {field.options.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  type={field.type === "number" ? "number" : "text"}
                  value={values[field.name] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [field.name]: e.target.value }))
                  }
                  placeholder={field.placeholder}
                  className="border-copper/15 bg-white/[0.02] text-ivory/90"
                />
              )}
            </div>
          ))}
          <Button
            type="submit"
            size="sm"
            disabled={loading}
            className="border-copper/30 bg-copper/10 hover:bg-copper/20"
            variant="outline"
          >
            {loading ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : null}
            {submitLabel}
          </Button>
        </form>
        {result ? (
          <pre className="mt-4 max-h-64 overflow-auto rounded-lg border border-copper/10 bg-obsidian-deep/70 p-3 font-mono text-xs text-ivory/80 whitespace-pre-wrap">
            {result}
          </pre>
        ) : null}
      </CardContent>
    </Card>
  );
}

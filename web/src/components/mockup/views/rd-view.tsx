"use client";

import type { ConsoleDepartment } from "@/lib/console/types";
import { ProtoRdBrainstorm } from "../prototype/proto-rd-brainstorm";

interface RdViewProps {
  department: ConsoleDepartment;
}

/** Contenu R&D — shell ChatGPT fourni par ProtoFullShell. */
export function MockupRdView({ department }: RdViewProps) {
  void department;
  return <ProtoRdBrainstorm />;
}

"use client";

import type { ConsoleDepartment } from "@/lib/console/types";
import { ProtoRdBrainstorm } from "../prototype/proto-rd-brainstorm";

interface RdViewProps {
  department: ConsoleDepartment;
}

/** Contenu R&D — copie pixel-près maquette ChatGPT / prototype Vite. */
export function MockupRdView({ department }: RdViewProps) {
  void department;
  return <ProtoRdBrainstorm />;
}

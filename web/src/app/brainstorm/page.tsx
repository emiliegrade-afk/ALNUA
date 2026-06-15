import { redirect } from "next/navigation";

/** Legacy path — Brainstorm lives in the R&D bureau (/rd, tab brainstorm). */
export default function BrainstormPage() {
  redirect("/rd?tab=brainstorm");
}

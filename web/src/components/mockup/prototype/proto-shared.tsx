"use client";

import { MoreHorizontal } from "lucide-react";
import { agents, type ProtoAgent } from "./proto-data";

export function ProtoAvatar({
  agent = "aria",
  size = "sm",
}: {
  agent?: string | ProtoAgent;
  size?: "sm" | "md";
}) {
  const a = typeof agent === "string" ? agents.find((x) => x.id === agent) : agent;
  return (
    <div className={`avatar ${size} avatar-${a?.color || "rose"}`}>
      {a?.initials || "AL"}
    </div>
  );
}

export function ProtoProgressRing({ value, small = false }: { value: number; small?: boolean }) {
  return (
    <div className={`progress-ring ${small ? "small" : ""}`} style={{ ["--p" as string]: `${value * 3.6}deg` }}>
      <span>{value}%</span>
    </div>
  );
}

export function ProtoPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="panel">
      <div className="panel-title">
        <span>{title}</span>
        <MoreHorizontal size={15} />
      </div>
      {children}
    </section>
  );
}

export function ProtoSectionHeader({
  title,
  desc,
  icon,
  children,
}: {
  title: string;
  desc: string;
  icon: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <div className="section-header">
      <div className="section-title">
        <div className="section-icon">{icon}</div>
        <div>
          <h1>{title}</h1>
          <p>{desc}</p>
        </div>
      </div>
      <div className="section-actions">{children}</div>
    </div>
  );
}

export function ProtoShell({ children }: { children: React.ReactNode }) {
  return <div className="alnua-dept-proto pb-20">{children}</div>;
}

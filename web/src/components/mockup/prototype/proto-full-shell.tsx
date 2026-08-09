"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bell,
  Bot,
  BriefcaseBusiness,
  ClipboardList,
  Code2,
  FlaskConical,
  Gauge,
  Grid2X2,
  Map,
  MessageCircle,
  Plus,
  Search,
  Sparkles,
  Target,
  Users,
  Zap,
} from "lucide-react";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { ProtoAvatar } from "./proto-shared";
import {
  PROTO_DEPT_HREF,
  PROTO_PATH_TO_DEPT,
  type ProtoDeptName,
} from "./proto-dept-routes";

const DEPARTMENTS: [string, ProtoDeptName, React.ComponentType<{ size?: number }>][] = [
  ["01", "Direction", BriefcaseBusiness],
  ["02", "Secrétariat", ClipboardList],
  ["03", "CEO", Target],
  ["04", "R&D", FlaskConical],
  ["05", "APP", Code2],
  ["06", "Gaming", Grid2X2],
  ["07", "Robotique", Bot],
  ["08", "Marketing", Activity],
  ["09", "Comptabilité", BarChart3],
  ["10", "Analytics", Gauge],
  ["11", "Brand Design", Sparkles],
];

const SUBTITLES: Partial<Record<ProtoDeptName, string>> = {
  "R&D": "Recherche · Idéation · Prototypes · Innovation",
  APP: "Développement de nos produits digitaux",
  Comptabilité: "Finance · Budget · Reporting · Conformité",
  Marketing: "Stratégie · Communication · Croissance",
};

function useLiveClock(): string {
  const [now, setNow] = useState("--:--:--");
  useEffect(() => {
    const tick = () =>
      setNow(new Date().toLocaleTimeString("fr-FR", { hour12: false }));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function ChatGptSidebar({ department }: { department: ProtoDeptName }) {
  const router = useRouter();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <AlnuaStar size={22} glow />
        </div>
        <div>
          <b>ALNUA</b>
          <span>VIRTUAL AI ENTERPRISE</span>
        </div>
      </div>

      <div className="side-label">VUE GLOBALE</div>
      <nav className="main-nav">
        <button type="button" className="nav-item" onClick={() => router.push("/agents")}>
          <Users size={16} />
          Tous les agents
        </button>
        <button type="button" className="nav-item" onClick={() => router.push("/activity")}>
          <Activity size={16} />
          Activité
        </button>
        <button type="button" className="nav-item" onClick={() => router.push("/")}>
          <Map size={16} />
          Vue HQ
        </button>
      </nav>

      <div className="side-label">PÔLES · 11</div>
      <div className="dept-list">
        {DEPARTMENTS.map(([n, name, Icon]) => (
          <button
            key={name}
            type="button"
            className={`dept ${department === name ? "selected" : ""}`}
            onClick={() => router.push(PROTO_DEPT_HREF[name])}
          >
            <Icon size={16} />
            <span>
              {n}&nbsp;&nbsp;{name}
            </span>
          </button>
        ))}
      </div>

      <div className="sidebar-bottom">
        <div className="user" style={{ margin: "0 4px 10px", padding: "8px 6px" }}>
          <ProtoAvatar size="sm" />
          <span>
            <b>Émilie Grade</b>
            <small>Fondatrice &amp; CEO</small>
          </span>
        </div>
      </div>
    </aside>
  );
}

function ChatGptTopbar({ department }: { department: ProtoDeptName }) {
  const time = useLiveClock();
  const subtitle =
    SUBTITLES[department] ?? "Opérations · Projets · Équipes · Performance";

  return (
    <header className="topbar">
      <div className="top-title">
        <strong style={{ color: "var(--copper2)", letterSpacing: "0.06em" }}>
          PÔLE {department.toUpperCase()}
        </strong>
        <span className="subtitle">{subtitle}</span>
      </div>
      <div className="top-actions">
        <div className="search">
          <Search size={15} />
          <input placeholder="Rechercher... (⌘K)" readOnly />
        </div>
        <button type="button" className="status-pill">
          <Zap size={14} /> Connexions <b>3</b>
        </button>
        <button type="button" className="status-pill online">
          <span className="dot green" /> Hub connecté <small>{time}</small>
        </button>
        <button type="button" className="primary-btn">
          <Plus size={15} /> Créer
        </button>
        <button type="button" className="outline-btn">
          <MessageCircle size={15} /> Assistants
        </button>
        <button type="button" className="icon-btn">
          <Bell size={16} />
        </button>
        <button type="button" className="outline-btn">
          Carte HQ
        </button>
      </div>
    </header>
  );
}

/** Shell 100% calqué sur les maquettes ChatGPT (logo ALNUA réel uniquement). */
export function ProtoFullShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const department = PROTO_PATH_TO_DEPT[pathname] ?? "APP";

  return (
    <div className="alnua-proto-root">
      <div className="app-shell">
        <ChatGptSidebar department={department} />
        <main className="main">
          <ChatGptTopbar department={department} />
          <div className="page">{children}</div>
        </main>
      </div>
    </div>
  );
}

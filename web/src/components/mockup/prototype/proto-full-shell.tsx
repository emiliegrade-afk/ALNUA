"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  BriefcaseBusiness,
  ClipboardList,
  Code2,
  FileText,
  FlaskConical,
  Gauge,
  Grid2X2,
  Lightbulb,
  Map,
  MessageCircle,
  Plus,
  Search,
  Settings2,
  Sparkles,
  Target,
  Workflow,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { AlnuaStar } from "@/components/brand/alnua-star";
import {
  PROTO_DEPT_HREF,
  PROTO_PATH_TO_DEPT,
  type ProtoDeptName,
} from "./proto-dept-routes";

const DEPARTMENTS: [string, ProtoDeptName, LucideIcon][] = [
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
  Gaming: "Studios · Builds · Lore · Assets",
  Robotique: "Hardware · Firmware · Simulation · Safety",
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

      <div className="side-label">TABLEAU DE BORD</div>
      <nav className="main-nav">
        <button type="button" className="nav-item" onClick={() => router.push("/")}>
          <Target size={16} />
          Command Center
        </button>
        <button type="button" className="nav-item" onClick={() => router.push("/activity")}>
          <Activity size={16} />
          Activité en direct
        </button>
        <button type="button" className="nav-item" onClick={() => router.push("/ceo")}>
          <ClipboardList size={16} />
          Décisions
          <b
            style={{
              marginLeft: "auto",
              background: "rgba(201,134,88,.2)",
              color: "var(--copper2)",
              borderRadius: 4,
              padding: "1px 5px",
              fontSize: 8,
            }}
          >
            2
          </b>
        </button>
      </nav>

      <div className="side-label">DÉPARTEMENTS</div>
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

      <div className="side-label">OUTILS</div>
      <nav className="main-nav" style={{ marginBottom: 8 }}>
        <button type="button" className="nav-item" onClick={() => router.push("/docs")}>
          <FileText size={16} />
          Documents
        </button>
        <button type="button" className="nav-item" onClick={() => router.push("/library")}>
          <BookOpen size={16} />
          Connaissances
        </button>
        <button type="button" className="nav-item" onClick={() => router.push("/settings")}>
          <Settings2 size={16} />
          Modèles
        </button>
        <button type="button" className="nav-item" onClick={() => router.push("/settings")}>
          <Workflow size={16} />
          Automatisations
        </button>
      </nav>

      <div className="sidebar-bottom">
        <div className="system-card">
          <div className="orbit">
            <AlnuaStar size={18} glow />
          </div>
          <div>
            <b>ALNUA CORE</b>
            <span>Système opérationnel</span>
          </div>
        </div>
        <div className="system-row">
          <span>
            <i className="dot green" /> Tous les systèmes
          </span>
          <b>opérationnels</b>
        </div>
      </div>
    </aside>
  );
}

function ChatGptTopbar({ department }: { department: ProtoDeptName }) {
  const time = useLiveClock();
  const router = useRouter();
  const subtitle =
    SUBTITLES[department] ?? "Opérations · Projets · Équipes · Performance";
  const isRd = department === "R&D";
  const isApp = department === "APP";
  const title = isApp ? "APP DEPARTMENT" : `PÔLE ${department.toUpperCase()}`;

  return (
    <header className="topbar">
      <div className="top-title">
        <strong style={{ color: "#e8e2da", letterSpacing: "0.08em", fontSize: 18 }}>
          {title}
        </strong>
        <span className="subtitle">{subtitle}</span>
      </div>
      <div className="top-actions">
        <div className="search">
          <Search size={15} />
          <input
            placeholder={
              isRd ? "Rechercher une idée, un dossier..." : "Rechercher... (⌘K)"
            }
            readOnly
          />
          <kbd>⌘ K</kbd>
        </div>
        <button type="button" className="status-pill">
          <Zap size={14} /> Connexions <b>3</b>
        </button>
        <button type="button" className="status-pill online">
          <span className="dot green" /> Hub connecté <small>{time}</small>
        </button>
        {isRd ? (
          <>
            <button type="button" className="primary-btn">
              <Plus size={15} /> Nouvelle idée
            </button>
            <button type="button" className="outline-btn">
              <Lightbulb size={15} /> Conseil IA
            </button>
          </>
        ) : (
          <button type="button" className="primary-btn">
            <Plus size={15} /> Créer
          </button>
        )}
        <button type="button" className="icon-btn">
          <Bell size={16} />
        </button>
        <div className="user">
          <div className="avatar sm avatar-rose">EG</div>
          <span>
            <b>Émilie Grade</b>
            <small>Fondatrice &amp; CEO</small>
          </span>
        </div>
        <button type="button" className="outline-btn" onClick={() => router.push("/")}>
          <Map size={14} /> Carte HQ
        </button>
      </div>
    </header>
  );
}

/** Shell calqué sur les maquettes ChatGPT (logo ALNUA réel). */
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
      <div className="floating-assistant">
        <MessageCircle size={17} />
        <span>Que souhaitez-vous faire aujourd&apos;hui ?</span>
        <button type="button" aria-label="Assistant">
          <Sparkles size={17} />
        </button>
      </div>
    </div>
  );
}

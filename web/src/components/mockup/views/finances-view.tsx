"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { ConsoleDepartment } from "@/lib/console/types";
import { FinancesDashboard } from "./finances-dashboard";
import { FINANCES_TABS, type FinancesTab } from "./finances-data";

export type { FinancesTab };

interface FinancesViewProps {
  department: ConsoleDepartment;
}

export function MockupFinancesView({ department }: FinancesViewProps) {
  void department;
  const [tab, setTab] = useState<FinancesTab>("Dashboard");

  return (
    <div className="pb-8">
      <div className="department-tabs" style={{ padding: 0, marginBottom: 14 }}>
        <div className="tabs">
          {FINANCES_TABS.map((t) => (
            <button
              key={t}
              type="button"
              className={tab === t ? "active" : undefined}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
        >
          {tab === "Dashboard" ? (
            <FinancesDashboard onNavigateTab={setTab} />
          ) : (
            <div className="panel" style={{ padding: 40, textAlign: "center" }}>
              <p style={{ fontSize: 14, color: "#e8e2da" }}>{tab}</p>
              <p style={{ marginTop: 8, fontSize: 11, color: "#747b83" }}>
                Maquette visuelle — branchement prévu (Phase 38 ROADMAP).
              </p>
              <button
                type="button"
                onClick={() => setTab("Dashboard")}
                className="text-btn"
                style={{ marginTop: 16, border: 0 }}
              >
                ← Retour Dashboard
              </button>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { ConsoleDepartment } from "@/lib/console/types";
import { PoleFilledPanel, PoleListCard, PoleStatStrip } from "../pole-proto-tabs";
import { FinancesDashboard } from "./finances-dashboard";
import { FINANCES_TABS, type FinancesTab } from "./finances-data";
import { FINANCES_SECONDARY } from "./finances-secondary";

export type { FinancesTab };

interface FinancesViewProps {
  department: ConsoleDepartment;
}

export function MockupFinancesView({ department }: FinancesViewProps) {
  void department;
  const [tab, setTab] = useState<FinancesTab>("Dashboard");
  const panel = FINANCES_SECONDARY[tab];

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
          ) : panel ? (
            <PoleFilledPanel
              title={panel.title}
              subtitle={panel.subtitle}
              onBack={() => setTab("Dashboard")}
            >
              <PoleStatStrip items={panel.stats} />
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                <PoleListCard title={panel.left.title} rows={panel.left.rows} />
                <PoleListCard title={panel.right.title} rows={panel.right.rows} />
              </div>
            </PoleFilledPanel>
          ) : null}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { X } from "lucide-react";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { useCooStore } from "@/store/coo-store";
import { cn } from "@/lib/utils";

export function CooDrawer() {
  const pathname = usePathname();
  const isOpen = useCooStore((s) => s.isDrawerOpen);
  const openDrawer = useCooStore((s) => s.openDrawer);
  const closeDrawer = useCooStore((s) => s.closeDrawer);
  const prefill = useCooStore((s) => s.prefillMessage);
  const clearPrefill = useCooStore((s) => s.clearPrefillMessage);

  useEffect(() => {
    if (prefill) openDrawer();
  }, [prefill, openDrawer]);

  useEffect(() => {
    closeDrawer();
  }, [pathname, closeDrawer]);

  function handleClose() {
    closeDrawer();
    clearPrefill();
  }

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-obsidian/80 backdrop-blur-sm"
          onClick={handleClose}
          aria-hidden
        />
      )}

      <div
        className={cn(
          "fixed right-0 top-0 bottom-0 z-50 w-full max-w-md",
          "bg-[#0E1014] border-l border-[#C08A72]/20",
          "shadow-[-8px_0_40px_rgba(0,0,0,0.5)]",
          "transition-transform duration-300",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#C08A72]/15">
          <div>
            <h3 className="font-['Space_Grotesk'] text-[#F5F2EA] font-medium">
              Aria & Nadia
            </h3>
            <p className="text-xs text-[#A7ADB5] mt-0.5">
              COO · Secrétariat · Langage naturel
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Fermer les assistants"
            className="text-[#A7ADB5] hover:text-[#F5F2EA] transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="h-[calc(100vh-72px)] overflow-hidden p-3">
          {isOpen ? <AssistantChat embedded /> : null}
        </div>
      </div>
    </>
  );
}

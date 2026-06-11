"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { MessageCircle, X } from "lucide-react";
import { COOChat } from "@/components/dashboard/coo-chat";
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
      <button
        type="button"
        onClick={openDrawer}
        aria-label="Ouvrir le chat COO"
        className={cn(
          "fixed bottom-6 right-6 z-50",
          "flex items-center gap-2 px-4 py-3 rounded-full",
          "bg-[#C08A62] hover:bg-[#D4A882] text-[#0E1014]",
          "font-['Space_Grotesk'] font-medium text-sm",
          "shadow-[0_4px_24px_rgba(192,138,98,0.3)]",
          "transition-all duration-200",
          isOpen && "opacity-0 pointer-events-none"
        )}
      >
        <MessageCircle className="h-4 w-4" />
        COO
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          onClick={handleClose}
          aria-hidden
        />
      )}

      <div
        className={cn(
          "fixed right-0 top-0 bottom-0 z-50 w-full max-w-md",
          "bg-[#0E1014] border-l border-[#C08A62]/20",
          "shadow-[-8px_0_40px_rgba(0,0,0,0.5)]",
          "transition-transform duration-300",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#C08A62]/15">
          <div>
            <h3 className="font-['Space_Grotesk'] text-[#F5F2EA] font-medium">
              COO — Direction générale
            </h3>
            <p className="text-xs text-[#A7ADB5] mt-0.5">
              Déléguer · Lancer pipeline · Briefing
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Fermer le chat COO"
            className="text-[#A7ADB5] hover:text-[#F5F2EA] transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="h-[calc(100vh-72px)] overflow-hidden p-3">
          {isOpen ? <COOChat embedded /> : null}
        </div>
      </div>
    </>
  );
}

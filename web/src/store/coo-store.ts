import { create } from "zustand";

interface CooStore {
  prefillMessage: string | null;
  setPrefillMessage: (message: string) => void;
  clearPrefillMessage: () => void;
  consumePrefillMessage: () => string | null;
  isDrawerOpen: boolean;
  openDrawer: () => void;
  closeDrawer: () => void;
}

export const useCooStore = create<CooStore>((set, get) => ({
  prefillMessage: null,
  setPrefillMessage: (message) => set({ prefillMessage: message }),
  clearPrefillMessage: () => set({ prefillMessage: null }),
  consumePrefillMessage: () => {
    const msg = get().prefillMessage;
    if (msg) set({ prefillMessage: null });
    return msg;
  },
  isDrawerOpen: false,
  openDrawer: () => set({ isDrawerOpen: true }),
  closeDrawer: () => set({ isDrawerOpen: false }),
}));

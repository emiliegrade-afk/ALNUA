import { create } from "zustand";

interface CooStore {
  prefillMessage: string | null;
  setPrefillMessage: (message: string) => void;
  consumePrefillMessage: () => string | null;
}

export const useCooStore = create<CooStore>((set, get) => ({
  prefillMessage: null,
  setPrefillMessage: (message) => set({ prefillMessage: message }),
  consumePrefillMessage: () => {
    const msg = get().prefillMessage;
    if (msg) set({ prefillMessage: null });
    return msg;
  },
}));

import { create } from "zustand";
import { getTodayCaptureCount } from "@/lib/quick-capture";

interface QuickCaptureStore {
  open: boolean;
  todayCount: number;
  setOpen: (open: boolean) => void;
  toggle: () => void;
  refreshTodayCount: () => void;
  setTodayCount: (count: number) => void;
}

export const useQuickCaptureStore = create<QuickCaptureStore>((set) => ({
  open: false,
  todayCount: 0,
  setOpen: (open) => set({ open }),
  toggle: () => set((s) => ({ open: !s.open })),
  refreshTodayCount: () => set({ todayCount: getTodayCaptureCount() }),
  setTodayCount: (todayCount) => set({ todayCount }),
}));

import { create } from 'zustand'
import type { ChatMessage } from '@/types'

interface ChatState {
  cooOpen: boolean
  activeAgentId: string | null
  messages: Record<string, ChatMessage[]>
  setCooOpen: (open: boolean) => void
  setActiveAgent: (id: string | null) => void
  addMessage: (agentId: string, message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  clearMessages: (agentId: string) => void
}

let msgCounter = 0

export const useChatStore = create<ChatState>((set) => ({
  cooOpen: false,
  activeAgentId: null,
  messages: {},

  setCooOpen: (open) => set({ cooOpen: open, activeAgentId: open ? 'coo' : null }),

  setActiveAgent: (id) => set({ activeAgentId: id, cooOpen: id === 'coo' }),

  addMessage: (agentId, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [agentId]: [
          ...(state.messages[agentId] ?? []),
          {
            ...message,
            id: `msg-${++msgCounter}`,
            timestamp: new Date(),
          },
        ],
      },
    })),

  clearMessages: (agentId) =>
    set((state) => ({
      messages: { ...state.messages, [agentId]: [] },
    })),
}))

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { StatusBar } from '@/components/layout/StatusBar'
import { DashboardHome } from '@/components/dashboard/DashboardHome'
import { COOAvatar } from '@/components/avatars/COOAvatar'
import { AgentPanel } from '@/components/agents/AgentPanel'
import { AgentList } from '@/components/agents/AgentList'
import { IssuesList } from '@/components/pipeline/IssuesList'
import { PRsList } from '@/components/pipeline/PRsList'
import { PipelineLog } from '@/components/pipeline/PipelineLog'
import { AppBranch } from '@/components/branches/AppBranch'
import { GamingBranch } from '@/components/branches/GamingBranch'
import { RoboBranch } from '@/components/branches/RoboBranch'
import { useChatStore } from '@/stores/chatStore'
import { useState, type ReactNode } from 'react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

function AgentsPage() {
  const [selected, setSelected] = useState<string | null>(null)

  return (
    <div className="flex-1 overflow-auto p-6">
      <h1 className="text-xl font-heading font-semibold mb-4">Agents ALNUA</h1>
      <div className="max-w-lg">
        <AgentList onSelect={setSelected} selectedId={selected} />
      </div>
      {selected && <AgentPanel agentId={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}

function PipelinePage() {
  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      <h1 className="text-xl font-heading font-semibold">Pipeline Codage</h1>
      <IssuesList />
      <PRsList />
      <PipelineLog />
    </div>
  )
}

function BranchPage({ children, title }: { children: ReactNode; title: string }) {
  return (
    <div className="flex-1 overflow-auto p-6">
      <h1 className="text-xl font-heading font-semibold mb-6">{title}</h1>
      <div className="max-w-md">{children}</div>
    </div>
  )
}

function AppLayout() {
  const { cooOpen, setCooOpen } = useChatStore()

  return (
    <div className="relative flex flex-col h-screen overflow-hidden">
      <div className="alnua-bg-orbs" />
      <Header />
      <div className="flex flex-1 min-h-0 relative z-10">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Routes>
            <Route path="/" element={<DashboardHome />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route
              path="/branch/app"
              element={
                <BranchPage title="Pôle App">
                  <AppBranch />
                </BranchPage>
              }
            />
            <Route
              path="/branch/gaming"
              element={
                <BranchPage title="Pôle Gaming">
                  <GamingBranch />
                </BranchPage>
              }
            />
            <Route
              path="/branch/robo"
              element={
                <BranchPage title="Pôle Robotique">
                  <RoboBranch />
                </BranchPage>
              }
            />
          </Routes>
        </main>
      </div>
      <StatusBar />
      <COOAvatar onClick={() => setCooOpen(!cooOpen)} />
      {cooOpen && <AgentPanel agentId="coo" onClose={() => setCooOpen(false)} />}
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

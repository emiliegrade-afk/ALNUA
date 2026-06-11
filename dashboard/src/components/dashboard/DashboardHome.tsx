import { BriefCard } from './BriefCard'
import { PipelineStatus } from './PipelineStatus'
import { CostsChart } from './CostsChart'
import { AppBranch } from '@/components/branches/AppBranch'
import { GamingBranch } from '@/components/branches/GamingBranch'
import { RoboBranch } from '@/components/branches/RoboBranch'

export function DashboardHome() {
  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BriefCard />
        <PipelineStatus />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AppBranch />
        <GamingBranch />
        <RoboBranch />
      </div>

      <CostsChart />
    </div>
  )
}

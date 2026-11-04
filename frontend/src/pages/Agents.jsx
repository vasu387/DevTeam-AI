/**
 * Agents Page - Overview of all six AI agents.
 */

import { Cpu } from 'lucide-react'
import AgentPanel from '../components/AgentPanel'

export default function Agents() {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center gap-3 px-6 py-4 border-b border-gray-800/60 bg-dark-850/50 flex-shrink-0">
        <Cpu size={20} className="text-accent-purple" />
        <h1 className="text-base font-bold text-white">AI Agents</h1>
        <span className="ml-auto text-xs text-gray-500 bg-gray-800/40 border border-gray-700/40 px-2.5 py-1 rounded-full">
          6 agents configured
        </span>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-screen-xl mx-auto">
          <div className="mb-5 p-4 bg-gray-800/30 border border-gray-700/40 rounded-xl">
            <p className="text-sm text-gray-400 leading-relaxed">
              DevTeam AI uses a team of <span className="text-gray-200 font-medium">six specialized agents</span> built
              on CrewAI. Each agent has a distinct role in the software development lifecycle.
              Agent execution will be connected to <span className="text-gray-200 font-medium">Meta Muse Spark</span> in
              a future phase.
            </p>
          </div>
          <AgentPanel agentStatuses={null} />
        </div>
      </div>
    </div>
  )
}


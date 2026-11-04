/**
 * AgentPanel - Displays all 6 specialized AI agents and their statuses.
 * Status is driven by real data only; defaults to 'idle' with no fake activity.
 */

import AgentCard from './AgentCard'
import { Cpu } from 'lucide-react'

// Static agent definitions — status and activity come from parent (real data)
const AGENT_DEFINITIONS = [
  {
    id: 'product-manager',
    name: 'Product Manager',
    role: 'Requirement analysis and user story generation',
  },
  {
    id: 'software-architect',
    name: 'Software Architect',
    role: 'System design and technology stack selection',
  },
  {
    id: 'database-designer',
    name: 'Database Designer',
    role: 'Schema design, ER diagrams and data modeling',
  },
  {
    id: 'developer',
    name: 'Developer',
    role: 'Code generation across frontend and backend',
  },
  {
    id: 'testing-engineer',
    name: 'Testing Engineer',
    role: 'Unit tests, integration tests and test reports',
  },
  {
    id: 'code-reviewer',
    name: 'Code Reviewer',
    role: 'Code quality checks and best-practice review',
  },
]

// Default idle activity message shown before any project starts
const IDLE_ACTIVITY = 'Waiting for a project requirement to begin.'

export default function AgentPanel({ agentStatuses }) {
  // Merge static definitions with any real status data from backend
  const agents = AGENT_DEFINITIONS.map((def) => {
    const liveStatus = agentStatuses?.[def.id]
    return {
      ...def,
      status: liveStatus?.status || 'idle',
      activity: liveStatus?.activity || IDLE_ACTIVITY,
      progress: liveStatus?.progress ?? undefined,
    }
  })

  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="w-9 h-9 bg-gradient-to-br from-accent-purple to-brand-500 rounded-lg
          flex items-center justify-center">
          <Cpu size={18} className="text-white" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-gray-100">AI Agent Team</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Six specialized agents collaborate to build your software.
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-gray-500 bg-gray-800/60 border border-gray-700/40 px-2.5 py-1 rounded-full">
            {agents.filter((a) => a.status === 'running').length} active
          </span>
          <span className="text-xs text-gray-500 bg-gray-800/60 border border-gray-700/40 px-2.5 py-1 rounded-full">
            {agents.filter((a) => a.status === 'completed').length} done
          </span>
        </div>
      </div>

      {/* Agent grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {/* Footer note */}
      <p className="mt-4 text-xs text-gray-500 text-center">
        Powered by CrewAI sequential multi-agent execution with Meta Muse Spark.
      </p>
    </div>
  )
}


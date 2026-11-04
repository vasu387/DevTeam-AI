/**
 * AgentCard - Displays a single AI agent with its status and activity.
 * Never shows fake activity — status must come from real backend data.
 */

import StatusBadge from './StatusBadge'

const AGENT_COLORS = {
  'Product Manager': { icon: '🗂️', accent: 'from-blue-500/20 to-blue-600/5', border: 'border-blue-500/20' },
  'Software Architect': { icon: '🏗️', accent: 'from-purple-500/20 to-purple-600/5', border: 'border-purple-500/20' },
  'Database Designer': { icon: '🗄️', accent: 'from-cyan-500/20 to-cyan-600/5', border: 'border-cyan-500/20' },
  'Developer': { icon: '💻', accent: 'from-emerald-500/20 to-emerald-600/5', border: 'border-emerald-500/20' },
  'Testing Engineer': { icon: '🧪', accent: 'from-amber-500/20 to-amber-600/5', border: 'border-amber-500/20' },
  'Code Reviewer': { icon: '🔍', accent: 'from-red-500/20 to-red-600/5', border: 'border-red-500/20' },
}

export default function AgentCard({ agent }) {
  const { name, role, status, activity, progress } = agent
  const colorConfig = AGENT_COLORS[name] || AGENT_COLORS['Developer']

  return (
    <div
      className={`relative rounded-xl border bg-gradient-to-br ${colorConfig.accent} ${colorConfig.border}
        p-4 transition-all duration-200 hover:shadow-lg hover:shadow-black/20`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{colorConfig.icon}</span>
          <div>
            <h3 className="text-sm font-semibold text-gray-100">{name} Agent</h3>
            <p className="text-xs text-gray-500 mt-0.5">{role}</p>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Activity */}
      <div className="mt-2">
        <p className="text-xs text-gray-400 leading-relaxed">
          {activity}
        </p>
      </div>

      {/* Progress bar — only shown when real progress data is available */}
      {status === 'running' && typeof progress === 'number' && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}


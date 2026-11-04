/**
 * Sidebar - Navigation sidebar with project list and backend status.
 */

import { useState } from 'react'
import {
  Bot,
  LayoutDashboard,
  FolderOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  Plus,
  Clock,
  Cpu,
} from 'lucide-react'
import BackendStatus from './BackendStatus'

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard' },
  { icon: FolderOpen, label: 'Projects', id: 'projects' },
  { icon: Cpu, label: 'Agents', id: 'agents' },
  { icon: Settings, label: 'Settings', id: 'settings' },
]

export default function Sidebar({ activePage, onNavigate }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`flex flex-col bg-dark-850 border-r border-gray-800/60 transition-all duration-300
        ${collapsed ? 'w-16' : 'w-60'}`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-800/60">
        <div className="w-8 h-8 bg-gradient-to-br from-brand-500 to-accent-purple rounded-lg flex items-center justify-center flex-shrink-0">
          <Bot size={18} className="text-white" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <h1 className="text-sm font-bold text-white truncate">DevTeam AI</h1>
            <p className="text-xs text-gray-500 truncate">Multi-Agent Platform</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto text-gray-600 hover:text-gray-300 transition-colors flex-shrink-0"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* New Project button */}
      <div className="px-3 pt-4 pb-2">
        <button
          onClick={() => onNavigate('dashboard')}
          className={`w-full flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white
            rounded-lg transition-colors font-medium text-sm
            ${collapsed ? 'justify-center p-2' : 'px-3 py-2.5'}`}
          title="New Project"
        >
          <Plus size={16} />
          {!collapsed && <span>New Project</span>}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ icon: Icon, label, id }) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
              transition-all duration-150
              ${
                activePage === id
                  ? 'text-brand-400 bg-brand-500/10 border border-brand-500/20'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800/60'
              }
              ${collapsed ? 'justify-center' : ''}`}
            title={collapsed ? label : undefined}
          >
            <Icon size={18} className="flex-shrink-0" />
            {!collapsed && <span>{label}</span>}
          </button>
        ))}
      </nav>

      {/* Recent Projects placeholder */}
      {!collapsed && (
        <div className="px-3 py-3 border-t border-gray-800/60">
          <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2 px-1">
            Recent
          </p>
          <div className="flex items-center gap-2 px-1 py-1.5 text-gray-600 text-xs">
            <Clock size={12} />
            <span>No recent projects</span>
          </div>
        </div>
      )}

      {/* Backend status */}
      {!collapsed && <BackendStatus />}
    </aside>
  )
}


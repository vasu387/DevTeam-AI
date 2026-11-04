/**
 * Settings Page - Application settings placeholder.
 */

import { Settings as SettingsIcon, Lock, Server, Palette } from 'lucide-react'

export default function Settings() {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center gap-3 px-6 py-4 border-b border-gray-800/60 bg-dark-850/50 flex-shrink-0">
        <SettingsIcon size={20} className="text-gray-400" />
        <h1 className="text-base font-bold text-white">Settings</h1>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-4">
          {[
            {
              icon: Server,
              title: 'Backend Configuration',
              desc: 'API endpoint and connection settings',
              color: 'text-brand-400',
            },
            {
              icon: Lock,
              title: 'API Keys',
              desc: 'Configure Meta Muse Spark and other API credentials (future phase)',
              color: 'text-accent-purple',
            },
            {
              icon: Palette,
              title: 'Appearance',
              desc: 'Theme and display preferences',
              color: 'text-accent-cyan',
            },
          ].map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="glass-card p-4 flex items-center gap-4 opacity-60">
              <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
                <Icon size={18} className={color} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
              </div>
              <span className="ml-auto text-xs text-gray-600 bg-gray-800/60 border border-gray-700/40 px-2 py-1 rounded-full flex-shrink-0">
                Coming soon
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}


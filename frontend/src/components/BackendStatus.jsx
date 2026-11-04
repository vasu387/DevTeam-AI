/**
 * BackendStatus - Shows real-time backend connectivity status in the sidebar.
 */

import { useState, useEffect, useCallback } from 'react'
import { checkHealth } from '../services/api'
import { Wifi, WifiOff, RefreshCw } from 'lucide-react'

export default function BackendStatus() {
  const [status, setStatus] = useState('checking') // 'checking' | 'connected' | 'disconnected'
  const [info, setInfo] = useState(null)
  const [lastChecked, setLastChecked] = useState(null)

  const check = useCallback(async () => {
    setStatus('checking')
    try {
      const data = await checkHealth()
      setStatus('connected')
      setInfo(data)
    } catch {
      setStatus('disconnected')
      setInfo(null)
    }
    setLastChecked(new Date())
  }, [])

  useEffect(() => {
    check()
    const interval = setInterval(check, 30000) // re-check every 30s
    return () => clearInterval(interval)
  }, [check])

  const isConnected = status === 'connected'
  const isChecking = status === 'checking'

  return (
    <div className="mx-3 mb-3">
      <div
        className={`rounded-lg border p-3 transition-all duration-300 ${
          isConnected
            ? 'bg-emerald-500/5 border-emerald-500/20'
            : isChecking
            ? 'bg-gray-800/40 border-gray-700/40'
            : 'bg-red-500/5 border-red-500/20'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Wifi size={14} className="text-emerald-400" />
            ) : isChecking ? (
              <RefreshCw size={14} className="text-gray-400 animate-spin" />
            ) : (
              <WifiOff size={14} className="text-red-400" />
            )}
            <span
              className={`text-xs font-medium ${
                isConnected
                  ? 'text-emerald-400'
                  : isChecking
                  ? 'text-gray-400'
                  : 'text-red-400'
              }`}
            >
              {isConnected ? 'Backend Connected' : isChecking ? 'Connecting…' : 'Backend Offline'}
            </span>
          </div>
          {!isChecking && (
            <button
              onClick={check}
              className="text-gray-600 hover:text-gray-400 transition-colors"
              title="Retry connection"
            >
              <RefreshCw size={12} />
            </button>
          )}
        </div>

        {isConnected && info && (
          <div className="mt-2 space-y-0.5">
            <p className="text-xs text-gray-500">
              v{info.version} · {info.uptime}
            </p>
          </div>
        )}

        {status === 'disconnected' && (
          <p className="mt-1.5 text-xs text-gray-500">
            Start the backend at{' '}
            <code className="text-gray-400 font-mono">localhost:8000</code>
          </p>
        )}

        {lastChecked && (
          <p className="mt-1.5 text-xs text-gray-600">
            Last checked {lastChecked.toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  )
}


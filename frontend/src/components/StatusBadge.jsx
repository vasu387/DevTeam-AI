/**
 * StatusBadge - Displays agent or system status with a colored dot and label.
 */

const STATUS_CONFIG = {
  idle: {
    dot: 'bg-gray-500',
    text: 'text-gray-400',
    label: 'Idle',
    bg: 'bg-gray-800/40',
    border: 'border-gray-700/40',
  },
  running: {
    dot: 'bg-emerald-400 animate-pulse',
    text: 'text-emerald-400',
    label: 'Running',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
  },
  completed: {
    dot: 'bg-blue-400',
    text: 'text-blue-400',
    label: 'Completed',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
  },
  error: {
    dot: 'bg-red-400',
    text: 'text-red-400',
    label: 'Error',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
  },
  waiting: {
    dot: 'bg-amber-400 animate-pulse',
    text: 'text-amber-400',
    label: 'Waiting',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
  },
}

export default function StatusBadge({ status = 'idle', label }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.idle
  const displayLabel = label || config.label

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
        border ${config.bg} ${config.border} ${config.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {displayLabel}
    </span>
  )
}


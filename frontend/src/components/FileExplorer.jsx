/**
 * FileExplorer - Displays generated project files (empty state until a real project exists).
 */

import { useState } from 'react'
import {
  FolderOpen,
  Folder,
  FileText,
  FileCode2,
  Download,
  ChevronRight,
  ChevronDown,
  Package,
} from 'lucide-react'

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-16 px-6">
      <div className="w-16 h-16 rounded-2xl bg-gray-800/60 border border-gray-700/40 flex items-center justify-center mb-4">
        <Package size={28} className="text-gray-600" />
      </div>
      <h3 className="text-base font-semibold text-gray-300 mb-2">No Project Generated Yet</h3>
      <p className="text-sm text-gray-500 max-w-xs leading-relaxed">
        Describe your software in the{' '}
        <span className="text-brand-400">Requirement Input</span> section and start the
        build process. Generated project files will appear here.
      </p>
    </div>
  )
}

const FILE_ICONS = {
  py: <FileCode2 size={14} className="text-blue-400" />,
  js: <FileCode2 size={14} className="text-yellow-400" />,
  jsx: <FileCode2 size={14} className="text-cyan-400" />,
  ts: <FileCode2 size={14} className="text-blue-500" />,
  tsx: <FileCode2 size={14} className="text-cyan-500" />,
  json: <FileText size={14} className="text-amber-400" />,
  md: <FileText size={14} className="text-gray-400" />,
  default: <FileText size={14} className="text-gray-500" />,
}

function getFileIcon(filename) {
  const ext = filename.split('.').pop()
  return FILE_ICONS[ext] || FILE_ICONS.default
}

function FileNode({ node, depth = 0 }) {
  const [open, setOpen] = useState(depth < 2)
  const isFolder = node.type === 'folder'

  return (
    <div>
      <div
        className={`flex items-center gap-1.5 px-2 py-1 rounded hover:bg-gray-800/60
          cursor-pointer text-sm transition-colors`}
        style={{ paddingLeft: `${8 + depth * 16}px` }}
        onClick={() => isFolder && setOpen(!open)}
      >
        {isFolder ? (
          <>
            <span className="text-gray-500 w-3 flex-shrink-0">
              {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            </span>
            {open ? (
              <FolderOpen size={14} className="text-brand-400 flex-shrink-0" />
            ) : (
              <Folder size={14} className="text-brand-400 flex-shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-3 flex-shrink-0" />
            {getFileIcon(node.name)}
          </>
        )}
        <span className={`truncate ${isFolder ? 'text-gray-200 font-medium' : 'text-gray-400'}`}>
          {node.name}
        </span>
      </div>
      {isFolder && open && node.children && (
        <div>
          {node.children.map((child, i) => (
            <FileNode key={i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FileExplorer({ projectFiles, projectName, onDownload }) {
  const hasFiles = projectFiles && projectFiles.length > 0

  return (
    <div className="glass-card flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800/60">
        <div className="flex items-center gap-2">
          <FolderOpen size={16} className="text-brand-400" />
          <h2 className="text-sm font-semibold text-gray-200">
            {projectName || 'Project Explorer'}
          </h2>
          {hasFiles && (
            <span className="text-xs text-gray-500 font-mono">
              {projectFiles.length} items
            </span>
          )}
        </div>

        <button
          disabled={!hasFiles}
          onClick={onDownload}
          className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg
            bg-gray-800 border border-gray-700 text-gray-400
            disabled:opacity-40 disabled:cursor-not-allowed
            enabled:hover:bg-gray-700 enabled:hover:text-gray-200 transition-all"
          title={hasFiles ? 'Download project' : 'No project to download yet'}
        >
          <Download size={13} />
          Download
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {hasFiles ? (
          <div className="py-2">
            {projectFiles.map((node, i) => (
              <FileNode key={i} node={node} />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </div>
    </div>
  )
}


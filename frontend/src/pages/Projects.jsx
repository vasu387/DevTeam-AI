/**
 * Projects Page - Lists all generated projects available on disk or actively generating.
 * Dynamically displays real status: Ready, Building, Interrupted, Failed, or Incomplete.
 */

import { useState, useEffect } from 'react'
import {
  FolderOpen,
  Plus,
  Package,
  Download,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Clock,
  ArrowRight,
} from 'lucide-react'
import { listProjects, downloadProjectZip } from '../services/api'

function getProjectBadge(proj) {
  // 1. Ready: Completed with files and valid ZIP
  if (proj.status === 'completed' && proj.has_zip && proj.file_count > 0) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
        <CheckCircle2 size={10} />
        Ready
      </span>
    )
  }

  // 2. Active building in progress
  if (proj.status === 'running') {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
        <Loader2 size={10} className="animate-spin" />
        Building ({proj.progress || 0}%)
      </span>
    )
  }

  // 3. Queued in background worker
  if (proj.status === 'queued') {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full">
        <Clock size={10} />
        Queued
      </span>
    )
  }

  // 4. Interrupted (e.g. server restart)
  if (proj.status === 'interrupted') {
    return (
      <span
        className="inline-flex items-center gap-1 text-[11px] font-medium text-orange-400 bg-orange-500/10 border border-orange-500/20 px-2 py-0.5 rounded-full"
        title={proj.error_message || 'Workflow interrupted by server restart'}
      >
        <AlertTriangle size={10} />
        Interrupted
      </span>
    )
  }

  // 5. Failed with explicit error
  if (proj.status === 'failed') {
    return (
      <span
        className="inline-flex items-center gap-1 text-[11px] font-medium text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded-full"
        title={proj.error_message || 'Project generation failed'}
      >
        <AlertCircle size={10} />
        Failed
      </span>
    )
  }

  // 6. Default incomplete
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-gray-400 bg-gray-500/10 border border-gray-500/20 px-2 py-0.5 rounded-full">
      <AlertCircle size={10} />
      Incomplete
    </span>
  )
}

export default function Projects({ onNavigate }) {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchProjects() {
      try {
        const data = await listProjects()
        setProjects(data.projects || [])
      } catch (err) {
        console.error('Failed to load projects list:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchProjects()
  }, [])

  function handleResumeDashboard(jobId) {
    if (jobId) {
      localStorage.setItem('devteam_active_job_id', jobId)
    }
    onNavigate('dashboard')
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800/60 bg-dark-850/50 flex-shrink-0">
        <div className="flex items-center gap-3">
          <FolderOpen size={20} className="text-brand-400" />
          <h1 className="text-base font-bold text-white">Projects</h1>
          <span className="text-xs text-gray-500 bg-gray-800/60 border border-gray-700/40 px-2.5 py-1 rounded-full">
            {projects.length} recorded
          </span>
        </div>
        <button
          onClick={() => onNavigate('dashboard')}
          className="btn-primary flex items-center gap-2 text-sm"
        >
          <Plus size={15} />
          New Project
        </button>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">
            Loading projects...
          </div>
        ) : projects.length > 0 ? (
          <div className="max-w-screen-xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((proj) => {
              const isReady = proj.status === 'completed' && proj.has_zip && proj.file_count > 0
              const isRunning = proj.status === 'running'

              return (
                <div
                  key={proj.safe_name || proj.name}
                  className="glass-card p-5 flex flex-col justify-between hover:border-gray-700 transition-all"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-9 h-9 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                          <FolderOpen size={18} className="text-brand-400" />
                        </div>
                        <div>
                          <h3 className="text-sm font-semibold text-gray-100 truncate max-w-[200px]" title={proj.name}>
                            {proj.name}
                          </h3>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {proj.file_count > 0
                              ? `${proj.file_count} files generated`
                              : '0 files generated'}
                          </p>
                        </div>
                      </div>
                      {getProjectBadge(proj)}
                    </div>

                    {proj.error_message && (
                      <p className="text-xs text-red-300/80 bg-red-500/10 border border-red-500/20 rounded-lg p-2 mt-2 leading-relaxed">
                        {proj.error_message}
                      </p>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-gray-800/60 flex items-center justify-between">
                    <span className="text-xs text-gray-500 font-mono">
                      {proj.has_zip
                        ? `${(proj.zip_size_bytes / 1024).toFixed(1)} KB ZIP`
                        : 'Uncompressed (No ZIP)'}
                    </span>

                    <div className="flex items-center gap-2">
                      {isRunning && (
                        <button
                          onClick={() => handleResumeDashboard(proj.job_id)}
                          className="btn-secondary flex items-center gap-1 text-xs py-1.5 px-2.5 text-brand-300 hover:text-white"
                        >
                          <span>Live</span>
                          <ArrowRight size={12} />
                        </button>
                      )}

                      {proj.has_zip ? (
                        <button
                          onClick={() => downloadProjectZip(proj.safe_name || proj.name, `${proj.safe_name || proj.name}.zip`)}
                          className="btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"
                        >
                          <Download size={12} />
                          Download
                        </button>
                      ) : (
                        <button
                          disabled
                          className="opacity-40 cursor-not-allowed bg-gray-800 border border-gray-700/40 text-gray-500 flex items-center gap-1.5 text-xs py-1.5 px-3 rounded-lg"
                          title="No ZIP archive available"
                        >
                          <Download size={12} />
                          No ZIP
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center h-full">
            <div className="text-center max-w-sm">
              <div className="w-20 h-20 rounded-2xl bg-gray-800/60 border border-gray-700/40 flex items-center justify-center mx-auto mb-5">
                <Package size={36} className="text-gray-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-200 mb-2">No Projects Yet</h2>
              <p className="text-sm text-gray-500 leading-relaxed mb-5">
                You haven't generated any projects yet. Start by describing your software
                requirement on the Dashboard.
              </p>
              <button
                onClick={() => onNavigate('dashboard')}
                className="btn-primary flex items-center gap-2 mx-auto"
              >
                <Plus size={15} />
                Create First Project
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

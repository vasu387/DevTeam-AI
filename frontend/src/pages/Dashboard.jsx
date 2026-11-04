/**
 * Dashboard Page - Main workspace for DevTeam AI.
 * Fully integrated with FastAPI backend and real CrewAI agent execution.
 * Persists active job ID across page navigation and server reloads.
 */

import { useState, useEffect, useRef } from 'react'
import RequirementInput from '../components/RequirementInput'
import AgentPanel from '../components/AgentPanel'
import FileExplorer from '../components/FileExplorer'
import {
  generateProject,
  getProjectStatus,
  getProjectFiles,
  downloadProjectZip,
} from '../services/api'
import {
  Bot,
  Zap,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Download,
  RotateCcw,
} from 'lucide-react'

const ACTIVE_JOB_KEY = 'devteam_active_job_id'

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(false)
  const [agentStatuses, setAgentStatuses] = useState(null)
  const [projectFiles, setProjectFiles] = useState(null)
  const [currentProject, setCurrentProject] = useState(null)
  const [currentJobId, setCurrentJobId] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  const [overallProgress, setOverallProgress] = useState(0)
  const [currentActivity, setCurrentActivity] = useState(null)

  // Ref to track active polling to avoid stale state in timers
  const pollTimerRef = useRef(null)

  // 1. On Mount: Restore active job from localStorage and recover status
  useEffect(() => {
    const savedJobId = localStorage.getItem(ACTIVE_JOB_KEY)
    if (!savedJobId) return

    setCurrentJobId(savedJobId)
    setCurrentActivity('Recovering job status from backend...')

    getProjectStatus(savedJobId)
      .then((data) => {
        if (data.project_name) setCurrentProject(data.project_name)
        if (data.agents) setAgentStatuses(data.agents)
        if (typeof data.progress === 'number') setOverallProgress(data.progress)
        if (data.activity) setCurrentActivity(data.activity)

        if (data.status === 'running' || data.status === 'queued') {
          setIsLoading(true)
        } else if (data.status === 'completed') {
          setIsLoading(false)
          setOverallProgress(100)
          setSuccessMessage(
            `Project '${data.project_name || 'Project'}' was generated successfully! ${
              data.generated_files?.length || 0
            } files ready.`
          )
          getProjectFiles(savedJobId)
            .then((res) => setProjectFiles(res.files || []))
            .catch((err) => console.error('Failed to load file tree:', err))
        } else if (data.status === 'interrupted') {
          setIsLoading(false)
          setErrorMessage(
            data.error_message ||
              'Generation was interrupted by a server restart. Three agent outputs are safely stored in database.'
          )
        } else if (data.status === 'failed') {
          setIsLoading(false)
          setErrorMessage(data.error_message || 'Project generation failed.')
        }
      })
      .catch((err) => {
        console.warn('Could not restore previous job status:', err)
        setCurrentActivity(null)
      })
  }, [])

  // 2. Handle requirement submission to FastAPI backend
  async function handleStartBuild({ projectName, requirement }) {
    setIsLoading(true)
    setErrorMessage(null)
    setSuccessMessage(null)
    setProjectFiles(null)
    setCurrentProject(projectName)
    setOverallProgress(5)
    setCurrentActivity('Submitting requirement to backend...')

    try {
      const response = await generateProject({ projectName, requirement })
      const jobId = response.job_id
      setCurrentJobId(jobId)
      localStorage.setItem(ACTIVE_JOB_KEY, jobId)
      setCurrentActivity('Job registered. Launching six-agent development crew...')
    } catch (err) {
      setIsLoading(false)
      setErrorMessage(err.message || 'Failed to submit requirement to backend.')
      setCurrentActivity(null)
    }
  }

  // 3. Poll job status every 2 seconds while generation is running
  useEffect(() => {
    if (!currentJobId || !isLoading) {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current)
        pollTimerRef.current = null
      }
      return
    }

    async function pollStatus() {
      try {
        const data = await getProjectStatus(currentJobId)

        if (data.agents) {
          setAgentStatuses(data.agents)
        }

        if (typeof data.progress === 'number') {
          setOverallProgress(data.progress)
        }

        if (data.activity) {
          setCurrentActivity(data.activity)
        }

        // Job completed successfully
        if (data.status === 'completed') {
          setIsLoading(false)
          setOverallProgress(100)
          setSuccessMessage(
            `Project '${data.project_name || currentProject}' generated successfully! ${
              data.generated_files?.length || 0
            } files ready.`
          )

          // Fetch the generated file tree for FileExplorer
          try {
            const filesData = await getProjectFiles(currentJobId)
            setProjectFiles(filesData.files || [])
          } catch (fileErr) {
            console.error('Failed to load file tree:', fileErr)
          }
        }

        // Job interrupted
        if (data.status === 'interrupted') {
          setIsLoading(false)
          setErrorMessage(
            data.error_message || 'Workflow was interrupted by server restart.'
          )
        }

        // Job failed
        if (data.status === 'failed') {
          setIsLoading(false)
          setErrorMessage(
            data.error_message || data.activity || 'Project generation failed.'
          )
        }
      } catch (pollErr) {
        console.warn('Status polling error:', pollErr)
      }
    }

    // Immediate first poll
    pollStatus()

    // Interval every 2000ms (2 seconds)
    pollTimerRef.current = setInterval(pollStatus, 2000)

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current)
        pollTimerRef.current = null
      }
    }
  }, [currentJobId, isLoading, currentProject])

  // Handle ZIP download
  function handleDownload() {
    const target = currentJobId || currentProject
    if (!target) return
    downloadProjectZip(target, `${currentProject || 'project'}.zip`)
  }

  // Clear current active job and reset to fresh state
  function handleResetWorkspace() {
    localStorage.removeItem(ACTIVE_JOB_KEY)
    setCurrentJobId(null)
    setCurrentProject(null)
    setAgentStatuses(null)
    setProjectFiles(null)
    setErrorMessage(null)
    setSuccessMessage(null)
    setOverallProgress(0)
    setCurrentActivity(null)
    setIsLoading(false)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800/60 bg-dark-850/50 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-brand-500 to-accent-purple rounded-lg flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white">
              {currentProject || 'DevTeam AI'}
            </h1>
            <p className="text-xs text-gray-500">
              {currentProject
                ? currentJobId
                  ? `Active Job: ${currentJobId}`
                  : 'Project workspace'
                : 'Start a new project below'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {currentProject && !isLoading && (
            <button
              onClick={handleResetWorkspace}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200 bg-gray-800/60 hover:bg-gray-800 border border-gray-700/40 px-3 py-1.5 rounded-full transition-all"
              title="Clear active job and start fresh"
            >
              <RotateCcw size={12} />
              Reset View
            </button>
          )}

          {isLoading ? (
            <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-full font-medium">
              <Loader2 size={12} className="animate-spin text-emerald-400" />
              <span>Building ({overallProgress}%)</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-gray-400 bg-gray-800/40 border border-gray-700/40 px-3 py-1.5 rounded-full">
              <Zap size={12} className="text-brand-400" />
              Live Multi-Agent Platform
            </div>
          )}
        </div>
      </header>

      {/* Scrollable workspace */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6 max-w-screen-2xl mx-auto">

          {/* Error Banner */}
          {errorMessage && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <AlertCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-red-300">Generation Notice</h4>
                  <p className="text-xs text-red-200/80 mt-1 leading-relaxed">
                    {errorMessage}
                  </p>
                </div>
              </div>
              <button
                onClick={handleResetWorkspace}
                className="btn-secondary text-xs px-2.5 py-1 text-gray-300 hover:text-white"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Success Banner */}
          {successMessage && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 size={18} className="text-emerald-400 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold text-emerald-300">Build Complete</h4>
                  <p className="text-xs text-emerald-200/80 mt-0.5">
                    {successMessage}
                  </p>
                </div>
              </div>
              <button
                onClick={handleDownload}
                className="btn-primary flex items-center gap-1.5 text-xs px-3 py-1.5"
              >
                <Download size={13} />
                Download ZIP
              </button>
            </div>
          )}

          {/* Welcome banner — shown only before any project is selected */}
          {!currentProject && !isLoading && (
            <div className="relative overflow-hidden rounded-xl border border-brand-500/20
              bg-gradient-to-br from-brand-500/10 via-accent-purple/5 to-transparent p-6">
              <div className="relative z-10">
                <h2 className="text-xl font-bold text-white mb-2">
                  Welcome to DevTeam AI 🚀
                </h2>
                <p className="text-sm text-gray-400 max-w-2xl leading-relaxed">
                  Your AI-powered virtual software engineering team. Describe the application
                  you want to build below, and six specialized AI agents will collaborate
                  in real-time to design, develop, test and review your complete project.
                </p>
                <div className="flex flex-wrap gap-2 mt-4">
                  {[
                    'Product Manager',
                    'Software Architect',
                    'Database Designer',
                    'Developer',
                    'Testing Engineer',
                    'Code Reviewer',
                  ].map((role) => (
                    <span
                      key={role}
                      className="text-xs bg-gray-800/60 border border-gray-700/40 text-gray-400 px-2.5 py-1 rounded-full"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>
              <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />
            </div>
          )}

          {/* Active Live Progress Banner */}
          {isLoading && currentActivity && (
            <div className="rounded-xl border border-brand-500/30 bg-gradient-to-r from-brand-500/10 via-purple-500/10 to-transparent p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Loader2 size={16} className="animate-spin text-brand-400" />
                  <span className="text-sm font-semibold text-gray-200">
                    Live Agent Execution
                  </span>
                </div>
                <span className="text-xs font-mono font-medium text-brand-400">
                  {overallProgress}%
                </span>
              </div>
              <p className="text-xs text-gray-400 mb-3">
                {currentActivity}
              </p>
              <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 to-accent-purple rounded-full transition-all duration-500"
                  style={{ width: `${Math.max(5, overallProgress)}%` }}
                />
              </div>
            </div>
          )}

          {/* Two-column layout: input + file explorer */}
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
            <div className="xl:col-span-3">
              <RequirementInput onSubmit={handleStartBuild} isLoading={isLoading} />
            </div>
            <div className="xl:col-span-2 min-h-80">
              <FileExplorer
                projectFiles={projectFiles}
                projectName={currentProject}
                onDownload={handleDownload}
              />
            </div>
          </div>

          {/* Agent panel */}
          <AgentPanel agentStatuses={agentStatuses} />
        </div>
      </div>
    </div>
  )
}

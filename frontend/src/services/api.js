/**
 * DevTeam AI - API Service
 * Handles all communication with the FastAPI backend.
 */

import axios from 'axios'

export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for consistent error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

/**
 * Health check - confirms backend is running.
 * @returns {Promise<{ status: string, service: string, version: string, timestamp: string, uptime: string }>}
 */
export async function checkHealth() {
  return apiClient.get('/api/health')
}

/**
 * List all projects available on disk or actively generating.
 * @returns {Promise<{ projects: Array, total: number }>}
 */
export async function listProjects() {
  return apiClient.get('/api/projects')
}

/**
 * Submit requirement to start multi-agent generation.
 * @param {{ projectName: string, requirement: string }} payload
 * @returns {Promise<{ job_id: string, project_name: string, safe_project_name: string, status: string, message: string }>}
 */
export async function generateProject({ projectName, requirement }) {
  return apiClient.post('/api/projects/generate', {
    projectName,
    requirement,
  })
}

/**
 * Get real-time status and agent execution states for a job.
 * @param {string} jobId
 * @returns {Promise<object>}
 */
export async function getProjectStatus(jobId) {
  return apiClient.get(`/api/projects/status/${jobId}`)
}

/**
 * Fetch generated file tree for FileExplorer.
 * @param {string} jobIdOrName
 * @returns {Promise<{ project_name: string, files: Array, total_files: number }>}
 */
export async function getProjectFiles(jobIdOrName) {
  return apiClient.get(`/api/projects/files/${jobIdOrName}`)
}

/**
 * Returns direct download URL for project ZIP archive.
 * @param {string} jobIdOrName
 * @returns {string}
 */
export function getProjectDownloadUrl(jobIdOrName) {
  return `${BASE_URL}/api/projects/download/${jobIdOrName}`
}

/**
 * Trigger download of the completed project ZIP archive.
 * @param {string} jobIdOrName
 * @param {string} [filename]
 */
export function downloadProjectZip(jobIdOrName, filename) {
  const url = getProjectDownloadUrl(jobIdOrName)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename || `${jobIdOrName}.zip`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export default apiClient

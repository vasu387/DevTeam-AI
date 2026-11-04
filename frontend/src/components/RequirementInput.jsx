/**
 * RequirementInput - Large input form for describing the software project.
 */

import { useState } from 'react'
import { Sparkles, RotateCcw, AlertCircle } from 'lucide-react'

const EXAMPLE_REQUIREMENT =
  'Build a food delivery application with customer registration, restaurant listings, ' +
  'shopping cart, online ordering, payment integration and an admin dashboard for ' +
  'managing restaurants and orders.'

export default function RequirementInput({ onSubmit, isLoading }) {
  const [projectName, setProjectName] = useState('')
  const [requirement, setRequirement] = useState('')
  const [errors, setErrors] = useState({})

  function validate() {
    const newErrors = {}
    if (!projectName.trim()) newErrors.projectName = 'Project name is required.'
    else if (projectName.trim().length < 3) newErrors.projectName = 'Name must be at least 3 characters.'
    if (!requirement.trim()) newErrors.requirement = 'Please describe your project requirement.'
    else if (requirement.trim().length < 30) newErrors.requirement = 'Please provide more detail (at least 30 characters).'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!validate()) return
    onSubmit?.({ projectName: projectName.trim(), requirement: requirement.trim() })
  }

  function handleClear() {
    setProjectName('')
    setRequirement('')
    setErrors({})
  }

  function handleExample() {
    setProjectName('Food Delivery App')
    setRequirement(EXAMPLE_REQUIREMENT)
    setErrors({})
  }

  return (
    <div className="glass-card p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-accent-purple rounded-lg
          flex items-center justify-center">
          <Sparkles size={18} className="text-white" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-gray-100">Project Requirement</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Describe the software you want to build in natural language.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        {/* Project name */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-300 mb-1.5" htmlFor="projectName">
            Project Name <span className="text-red-400">*</span>
          </label>
          <input
            id="projectName"
            type="text"
            value={projectName}
            onChange={(e) => {
              setProjectName(e.target.value)
              if (errors.projectName) setErrors((prev) => ({ ...prev, projectName: undefined }))
            }}
            placeholder="e.g. Food Delivery App"
            className={`input-field ${errors.projectName ? 'border-red-500/60 focus:ring-red-500' : ''}`}
            disabled={isLoading}
          />
          {errors.projectName && (
            <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
              <AlertCircle size={12} />
              {errors.projectName}
            </p>
          )}
        </div>

        {/* Requirement textarea */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-300 mb-1.5" htmlFor="requirement">
            Requirement Description <span className="text-red-400">*</span>
          </label>
          <textarea
            id="requirement"
            value={requirement}
            onChange={(e) => {
              setRequirement(e.target.value)
              if (errors.requirement) setErrors((prev) => ({ ...prev, requirement: undefined }))
            }}
            rows={6}
            placeholder={`Describe what you want to build in detail...\n\nExample: "${EXAMPLE_REQUIREMENT}"`}
            className={`input-field resize-none font-sans leading-relaxed
              ${errors.requirement ? 'border-red-500/60 focus:ring-red-500' : ''}`}
            disabled={isLoading}
          />
          <div className="flex items-center justify-between mt-1.5">
            {errors.requirement ? (
              <p className="text-xs text-red-400 flex items-center gap-1">
                <AlertCircle size={12} />
                {errors.requirement}
              </p>
            ) : (
              <p className="text-xs text-gray-600">
                {requirement.length} characters
              </p>
            )}
            <button
              type="button"
              onClick={handleExample}
              className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
              disabled={isLoading}
            >
              Use example
            </button>
          </div>
        </div>

        {/* Note about real multi-agent generation */}
        <div className="mb-5 flex items-start gap-2 bg-brand-500/10 border border-brand-500/20
          rounded-lg px-3 py-2.5">
          <Sparkles size={14} className="text-brand-400 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-brand-300/80 leading-relaxed">
            <span className="font-medium">Live Multi-Agent Pipeline.</span>{' '}
            Submitting a requirement launches all six CrewAI agents powered by Meta Muse Spark.
            Generated source code and reports will appear in the Project Explorer upon completion.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary flex items-center gap-2 flex-1 justify-center"
          >
            <Sparkles size={16} />
            {isLoading ? 'Starting Build…' : 'Start Building'}
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={isLoading}
            className="btn-secondary flex items-center gap-2 px-4"
          >
            <RotateCcw size={14} />
            Clear
          </button>
        </div>
      </form>
    </div>
  )
}


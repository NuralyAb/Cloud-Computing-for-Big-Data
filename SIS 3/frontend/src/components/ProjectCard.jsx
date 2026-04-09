import { useState } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'
import StatusBadge from './StatusBadge'

export default function ProjectCard({ project, running, onRefresh }) {
  const [loading, setLoading] = useState(false)

  const maskedToken = project.telegram_token
    ? project.telegram_token.slice(0, 8) + '...' + project.telegram_token.slice(-4)
    : '***'

  const handleStart = async () => {
    setLoading(true)
    try {
      await api.post(`/api/projects/${project.id}/start`)
      toast.success('Bot started')
      onRefresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start bot')
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    setLoading(true)
    try {
      await api.post(`/api/projects/${project.id}/stop`)
      toast.success('Bot stopped')
      onRefresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to stop bot')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`Delete project "${project.name}"? This cannot be undone.`)) return
    setLoading(true)
    try {
      await api.delete(`/api/projects/${project.id}`)
      toast.success('Project deleted')
      onRefresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete project')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900 text-lg">{project.name}</h3>
          <p className="text-xs text-gray-400 mt-1 font-mono">{maskedToken}</p>
        </div>
        <StatusBadge running={running} />
      </div>

      <p className="text-xs text-gray-400">
        Table: <span className="font-mono">{project.table_name}</span>
      </p>

      <div className="flex gap-2 mt-auto pt-2">
        {!running ? (
          <button
            onClick={handleStart}
            disabled={loading}
            className="flex-1 bg-green-600 text-white text-sm py-2 rounded-lg hover:bg-green-700 transition disabled:opacity-50"
          >
            {loading ? '...' : 'Start'}
          </button>
        ) : (
          <button
            onClick={handleStop}
            disabled={loading}
            className="flex-1 bg-yellow-500 text-white text-sm py-2 rounded-lg hover:bg-yellow-600 transition disabled:opacity-50"
          >
            {loading ? '...' : 'Stop'}
          </button>
        )}
        <button
          onClick={handleDelete}
          disabled={loading}
          className="bg-red-50 text-red-600 text-sm py-2 px-4 rounded-lg hover:bg-red-100 transition disabled:opacity-50"
        >
          Delete
        </button>
      </div>
    </div>
  )
}

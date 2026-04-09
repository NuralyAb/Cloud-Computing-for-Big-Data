import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import ProjectCard from '../components/ProjectCard'

export default function HomePage() {
  const [projects, setProjects] = useState([])
  const [statuses, setStatuses] = useState({})
  const [loading, setLoading] = useState(true)

  const fetchProjects = useCallback(async () => {
    try {
      const res = await api.get('/api/projects')
      setProjects(res.data)
    } catch {
      // silently fail on poll
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchStatuses = useCallback(async () => {
    const newStatuses = {}
    await Promise.all(
      projects.map(async (p) => {
        try {
          const res = await api.get(`/api/projects/${p.id}/status`)
          newStatuses[p.id] = res.data.running
        } catch {
          newStatuses[p.id] = false
        }
      })
    )
    setStatuses(newStatuses)
  }, [projects])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  useEffect(() => {
    if (projects.length === 0) return
    fetchStatuses()
    const interval = setInterval(fetchStatuses, 5000)
    return () => clearInterval(interval)
  }, [projects, fetchStatuses])

  const handleRefresh = () => {
    fetchProjects()
    setTimeout(fetchStatuses, 500)
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-semibold text-gray-700 mb-2">No projects yet</h2>
        <p className="text-gray-400 mb-6">Create your first RAG-powered Telegram bot</p>
        <Link
          to="/create"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition"
        >
          Create Project
        </Link>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {projects.map((p) => (
        <ProjectCard
          key={p.id}
          project={p}
          running={statuses[p.id] || false}
          onRefresh={handleRefresh}
        />
      ))}
    </div>
  )
}

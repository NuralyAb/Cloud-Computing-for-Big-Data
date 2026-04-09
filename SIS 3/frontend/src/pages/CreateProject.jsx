import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../api/client'

export default function CreateProject() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [token, setToken] = useState('')
  const [knowledgeBase, setKnowledgeBase] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim() || !token.trim() || !knowledgeBase.trim()) {
      setError('All fields are required.')
      return
    }

    setLoading(true)
    try {
      await api.post('/api/projects', {
        name: name.trim(),
        telegram_token: token.trim(),
        knowledge_base: knowledgeBase.trim(),
      })
      toast.success('Project created and indexed!')
      navigate('/')
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to create project'
      setError(detail)
      toast.error(detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New Project</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Support Bot"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Telegram Bot Token</label>
          <div className="relative">
            <input
              type={showToken ? 'text' : 'password'}
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="123456789:ABCdefGhIJKlmNoPQRstuVWXyz"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 pr-16 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-700 px-2 py-1"
            >
              {showToken ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Knowledge Base</label>
          <textarea
            value={knowledgeBase}
            onChange={(e) => setKnowledgeBase(e.target.value)}
            placeholder="Paste your knowledge base text here..."
            rows={12}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
          />
          <p className="text-xs text-gray-400 mt-1">
            {knowledgeBase.length} characters
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          )}
          {loading ? 'Creating & Indexing...' : 'Create & Index'}
        </button>
      </form>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../api/client'

export default function CreateProject() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [token, setToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [ownerTgId, setOwnerTgId] = useState('')

  const [sourceType, setSourceType] = useState('text')
  const [knowledgeBase, setKnowledgeBase] = useState('')
  const [file, setFile] = useState(null)
  const [sourceUrl, setSourceUrl] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim() || !token.trim()) {
      setError('Project name and bot token are required.')
      return
    }
    if (sourceType === 'text' && !knowledgeBase.trim()) {
      setError('Knowledge base text is required.')
      return
    }
    if (sourceType === 'file' && !file) {
      setError('Please select a file.')
      return
    }
    if (sourceType === 'url' && !sourceUrl.trim()) {
      setError('Please enter a URL.')
      return
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('name', name.trim())
      formData.append('telegram_token', token.trim())
      formData.append('source_type', sourceType)
      if (ownerTgId.trim()) formData.append('owner_tg_id', ownerTgId.trim())
      if (sourceType === 'text') formData.append('knowledge_base', knowledgeBase.trim())
      if (sourceType === 'file') formData.append('file', file)
      if (sourceType === 'url') formData.append('source_url', sourceUrl.trim())

      await api.post('/api/projects', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      toast.success('Project created and indexed!')
      navigate('/')
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to create project'
      setError(typeof detail === 'string' ? detail : 'Invalid input')
      toast.error(typeof detail === 'string' ? detail : 'Failed to create project')
    } finally {
      setLoading(false)
    }
  }

  const tabClass = (active) =>
    `flex-1 py-2 px-3 text-sm font-medium rounded-lg transition ${
      active
        ? 'bg-blue-600 text-white'
        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
    }`

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
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              className="w-full border border-gray-300 rounded-lg px-3 py-2 pr-16 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Your Telegram ID <span className="text-gray-400 text-xs">(optional, for handoff notifications)</span>
          </label>
          <input
            type="text"
            value={ownerTgId}
            onChange={(e) => setOwnerTgId(e.target.value)}
            placeholder="123456789"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">
            Get your ID from <a href="https://t.me/userinfobot" target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">@userinfobot</a>. You'll get a Telegram notification when the bot can't answer a user.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Knowledge Base Source</label>
          <div className="flex gap-2 mb-4">
            <button type="button" className={tabClass(sourceType === 'text')} onClick={() => setSourceType('text')}>
              Paste text
            </button>
            <button type="button" className={tabClass(sourceType === 'file')} onClick={() => setSourceType('file')}>
              Upload file
            </button>
            <button type="button" className={tabClass(sourceType === 'url')} onClick={() => setSourceType('url')}>
              From URL
            </button>
          </div>

          {sourceType === 'text' && (
            <>
              <textarea
                value={knowledgeBase}
                onChange={(e) => setKnowledgeBase(e.target.value)}
                placeholder="Paste your knowledge base text here..."
                rows={12}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
              <p className="text-xs text-gray-400 mt-1">{knowledgeBase.length} characters</p>
            </>
          )}

          {sourceType === 'file' && (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-sm"
              />
              <p className="text-xs text-gray-400 mt-2">Supported: PDF, DOCX, TXT, MD</p>
              {file && (
                <p className="text-sm text-gray-600 mt-2">Selected: <span className="font-medium">{file.name}</span> ({(file.size / 1024).toFixed(1)} KB)</p>
              )}
            </div>
          )}

          {sourceType === 'url' && (
            <>
              <input
                type="url"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://example.com/about"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-400 mt-1">The page content will be extracted and used as knowledge base.</p>
            </>
          )}
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
          {loading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />}
          {loading ? 'Creating & Indexing...' : 'Create & Index'}
        </button>
      </form>
    </div>
  )
}

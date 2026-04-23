import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'

function StatCard({ label, value, color = 'blue' }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    purple: 'bg-purple-50 text-purple-700',
  }
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <div className={`inline-block text-xs font-medium px-2.5 py-1 rounded-full mb-3 ${colors[color]}`}>
        {label}
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
    </div>
  )
}

function ActivityChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <h3 className="font-semibold text-gray-900 mb-4">Activity (last 14 days)</h3>
        <p className="text-sm text-gray-400">No activity yet</p>
      </div>
    )
  }

  const max = Math.max(...data.map((d) => d.cnt), 1)

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Activity (last 14 days)</h3>
      <div className="flex items-end gap-1 h-40">
        {data.map((d) => (
          <div key={d.day} className="flex-1 flex flex-col items-center gap-1 group">
            <div className="relative w-full flex items-end h-full">
              <div
                className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition"
                style={{ height: `${(d.cnt / max) * 100}%` }}
                title={`${d.day}: ${d.cnt} msgs`}
              />
              <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-xs text-gray-600 opacity-0 group-hover:opacity-100 transition whitespace-nowrap">
                {d.cnt}
              </span>
            </div>
            <span className="text-[10px] text-gray-400 rotate-45 origin-top-left whitespace-nowrap">
              {d.day.slice(5)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [unanswered, setUnanswered] = useState([])
  const [loading, setLoading] = useState(true)
  const [showUnanswered, setShowUnanswered] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [p, a, u] = await Promise.all([
          api.get(`/api/projects/${projectId}`),
          api.get(`/api/projects/${projectId}/analytics`),
          api.get(`/api/projects/${projectId}/unanswered`),
        ])
        if (!cancelled) {
          setProject(p.data)
          setAnalytics(a.data)
          setUnanswered(u.data)
        }
      } catch {
        // ignore
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [projectId])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (!project || !analytics) {
    return <p className="text-gray-500">Project not found.</p>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/" className="text-sm text-gray-500 hover:text-gray-700">← Back to projects</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-2">{project.name}</h1>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Messages" value={analytics.total_messages} color="blue" />
        <StatCard label="Answered" value={analytics.answered} color="green" />
        <StatCard label="Unanswered" value={analytics.unanswered} color="red" />
        <StatCard label="Unique Users" value={analytics.unique_users} color="purple" />
      </div>

      <ActivityChart data={analytics.activity} />

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <h3 className="font-semibold text-gray-900 mb-4">Top Questions</h3>
        {analytics.top_questions.length === 0 ? (
          <p className="text-sm text-gray-400">No questions yet</p>
        ) : (
          <ol className="space-y-2">
            {analytics.top_questions.map((q, i) => (
              <li key={i} className="flex justify-between items-start gap-3 py-2 border-b border-gray-100 last:border-0">
                <div className="flex gap-3">
                  <span className="text-gray-400 font-mono text-sm w-6">{i + 1}.</span>
                  <span className="text-sm text-gray-700">{q.q}</span>
                </div>
                <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full font-medium whitespace-nowrap">
                  {q.cnt}x
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">
            Unanswered Questions
            {unanswered.length > 0 && (
              <span className="ml-2 bg-red-100 text-red-700 text-xs px-2 py-1 rounded-full">
                {unanswered.length}
              </span>
            )}
          </h3>
          {unanswered.length > 0 && (
            <button
              onClick={() => setShowUnanswered(!showUnanswered)}
              className="text-sm text-blue-600 hover:underline"
            >
              {showUnanswered ? 'Hide' : 'Show'}
            </button>
          )}
        </div>

        {unanswered.length === 0 ? (
          <p className="text-sm text-gray-400">
            Great — the bot answered every question. When customers ask things not in your knowledge base, they'll show up here so you can expand it.
          </p>
        ) : (
          <>
            <p className="text-sm text-gray-500 mb-3">
              These questions couldn't be answered. Consider adding them to your knowledge base.
            </p>
            {showUnanswered && (
              <ul className="space-y-2">
                {unanswered.map((u, i) => (
                  <li key={i} className="flex justify-between items-start gap-3 py-2 border-b border-gray-100 last:border-0">
                    <span className="text-sm text-gray-700">{u.question}</span>
                    <span className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded-full font-medium whitespace-nowrap">
                      {u.count}x
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </div>
  )
}

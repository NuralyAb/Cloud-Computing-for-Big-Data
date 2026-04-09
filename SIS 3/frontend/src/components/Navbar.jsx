import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-gray-900">
          RAG Bot Builder
        </Link>
        <Link
          to="/create"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
        >
          + New Project
        </Link>
      </div>
    </nav>
  )
}

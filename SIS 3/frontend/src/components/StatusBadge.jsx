export default function StatusBadge({ running }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
        running
          ? 'bg-green-100 text-green-700'
          : 'bg-gray-100 text-gray-500'
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          running ? 'bg-green-500' : 'bg-gray-400'
        }`}
      />
      {running ? 'Running' : 'Stopped'}
    </span>
  )
}

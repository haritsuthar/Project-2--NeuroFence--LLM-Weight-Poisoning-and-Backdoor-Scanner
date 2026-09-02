import { useEffect, useRef } from 'react'

const STATUS_DOT = {
  pending:  'bg-brand-muted',
  loading:  'bg-yellow-400',
  scanning: 'bg-blue-400 animate-pulse',
  done:     'bg-brand-green',
  error:    'bg-red-400',
}

export default function LogPanel({ lines, status }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  return (
    <div className="bg-brand-surface border border-brand-border rounded-xl overflow-hidden">
      <div className="px-4 py-2.5 border-b border-brand-border flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${STATUS_DOT[status] ?? STATUS_DOT.pending}`} />
        <h3 className="text-xs font-semibold text-brand-muted uppercase tracking-wider">
          Scan Log
        </h3>
      </div>
      <div className="max-h-56 overflow-y-auto p-4 font-mono text-xs text-brand-green leading-relaxed">
        {lines.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

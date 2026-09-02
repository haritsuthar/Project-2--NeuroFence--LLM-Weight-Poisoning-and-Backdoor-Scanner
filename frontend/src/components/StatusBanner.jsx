const STATUS_LABELS = {
  pending:  { label: 'Pending…',       color: 'text-brand-muted' },
  loading:  { label: 'Loading model…', color: 'text-yellow-400' },
  scanning: { label: 'Scanning…',      color: 'text-blue-400' },
  done:     { label: 'Complete',        color: 'text-brand-green' },
  error:    { label: 'Error',           color: 'text-red-400' },
}

export default function StatusBanner({ job }) {
  const { label, color } = STATUS_LABELS[job.status] || STATUS_LABELS.pending
  const pct = job.progress ?? 0

  return (
    <div className="bg-brand-surface border border-brand-border rounded-xl p-4 space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className={`font-semibold ${color}`}>{label}</span>
        <span className="text-brand-muted font-mono text-xs">{pct}%</span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-brand-bg rounded-full h-2 overflow-hidden">
        <div
          className="h-2 rounded-full bg-brand-accent transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

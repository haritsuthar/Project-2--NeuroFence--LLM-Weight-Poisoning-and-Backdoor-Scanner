function riskMeta(score) {
  if (score < 1.0) return { label: 'LOW',      bg: 'bg-green-900/60',  border: 'border-green-600', text: 'text-green-300',  ring: 'ring-green-500' }
  if (score < 3.0) return { label: 'MEDIUM',   bg: 'bg-yellow-900/60', border: 'border-yellow-600',text: 'text-yellow-300', ring: 'ring-yellow-500' }
  if (score < 6.0) return { label: 'HIGH',     bg: 'bg-orange-900/60', border: 'border-orange-600',text: 'text-orange-300', ring: 'ring-orange-500' }
  return              { label: 'CRITICAL', bg: 'bg-red-900/60',    border: 'border-red-600',   text: 'text-red-300',    ring: 'ring-red-500' }
}

export default function RiskBadge({ score }) {
  const { label, bg, border, text, ring } = riskMeta(score ?? 0)

  return (
    <div className={`${bg} border ${border} rounded-xl p-5 flex flex-col items-center justify-center gap-1 ring-1 ${ring}/30 h-full`}>
      <p className="text-brand-muted text-xs uppercase tracking-widest">Risk Score</p>
      <p className={`text-4xl font-bold font-mono ${text}`}>
        {(score ?? 0).toFixed(3)}
      </p>
      <span className={`text-sm font-semibold px-3 py-1 rounded-full border ${border} ${text} mt-1`}>
        {label}
      </span>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between text-sm py-1.5 border-b border-brand-border last:border-0">
      <span className="text-brand-muted">{label}</span>
      <span className="text-brand-text font-mono text-xs break-all max-w-[60%] text-right">
        {value ?? '—'}
      </span>
    </div>
  )
}

export default function ModelInfoCard({ info }) {
  if (!info) return null

  const sha = info.sha256 ?? 'n/a'
  const shortSha = sha !== 'n/a' ? sha.slice(0, 16) + '…' : 'n/a'

  return (
    <div className="bg-brand-surface border border-brand-border rounded-xl p-5 h-full">
      <h3 className="text-sm font-semibold text-brand-text mb-3">Model Information</h3>
      <Row label="Type"       value={info.model_type} />
      <Row label="Parameters" value={info.num_parameters?.toLocaleString()} />
      <Row label="Device"     value={info.device} />
      <Row label="Hidden Size"value={info.hidden_size} />
      <Row label="Layers"     value={info.num_layers} />
      <Row label="SHA-256"    value={shortSha} />
    </div>
  )
}

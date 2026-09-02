export default function Header() {
  return (
    <header className="border-b border-brand-border bg-brand-surface/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-brand-accent tracking-tight">
            ⬡ NeuroFence
          </span>
          <span className="hidden sm:inline text-brand-muted text-sm border border-brand-border rounded px-2 py-0.5">
            LLM Backdoor Scanner
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-brand-muted">
          <span className="w-2 h-2 rounded-full bg-brand-green animate-pulse" />
          Offline Mode
        </div>
      </div>
    </header>
  )
}

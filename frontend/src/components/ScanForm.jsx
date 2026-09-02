import { useState } from 'react'

export default function ScanForm({ onScan, scanning }) {
  const [modelPath, setModelPath] = useState('')
  const [numPrompts, setNumPrompts] = useState(200)
  const [scanLimit, setScanLimit] = useState(60)

  function handleSubmit(e) {
    e.preventDefault()
    if (!modelPath.trim()) return
    onScan({ modelPath: modelPath.trim(), numPrompts, scanLimit })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-brand-surface border border-brand-border rounded-xl p-5 space-y-4"
    >
      <h2 className="text-base font-semibold text-brand-text">Configure Scan</h2>

      <div className="space-y-1">
        <label className="text-xs text-brand-muted font-medium uppercase tracking-wide">
          Model Path
        </label>
        <input
          type="text"
          value={modelPath}
          onChange={e => setModelPath(e.target.value)}
          placeholder="e.g. C:\models\tinyllama-1b"
          className="w-full bg-brand-bg border border-brand-border rounded-lg px-3 py-2 text-sm text-brand-text placeholder:text-brand-muted focus:outline-none focus:border-brand-accent"
          required
          disabled={scanning}
        />
        <p className="text-xs text-brand-muted">
          Absolute path to a local Hugging Face model folder (must contain config.json).
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-xs text-brand-muted font-medium uppercase tracking-wide">
            Prompts Generated
          </label>
          <input
            type="number"
            min={10}
            max={2000}
            value={numPrompts}
            onChange={e => setNumPrompts(Number(e.target.value))}
            className="w-full bg-brand-bg border border-brand-border rounded-lg px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-accent"
            disabled={scanning}
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-brand-muted font-medium uppercase tracking-wide">
            Prompts Scanned
          </label>
          <input
            type="number"
            min={5}
            max={500}
            value={scanLimit}
            onChange={e => setScanLimit(Number(e.target.value))}
            className="w-full bg-brand-bg border border-brand-border rounded-lg px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-accent"
            disabled={scanning}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={scanning || !modelPath.trim()}
        className="w-full bg-brand-accent hover:bg-orange-400 disabled:opacity-40 disabled:cursor-not-allowed text-brand-bg font-semibold py-2.5 rounded-lg text-sm transition-colors"
      >
        {scanning ? 'Scanning…' : '▶  Run Scan'}
      </button>
    </form>
  )
}

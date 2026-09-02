import { useState } from 'react'
import { heatmapUrl } from '../api'

export default function HeatmapPanel({ jobId }) {
  const [loaded, setLoaded] = useState(false)
  const [errored, setErrored] = useState(false)
  const url = heatmapUrl(jobId)

  return (
    <div className="bg-brand-surface border border-brand-border rounded-xl p-5">
      <h3 className="text-sm font-semibold text-brand-text mb-3">
        Activation Heatmap
      </h3>
      {errored ? (
        <p className="text-brand-muted text-sm">Heatmap could not be loaded.</p>
      ) : (
        <div className="relative">
          {!loaded && (
            <div className="absolute inset-0 flex items-center justify-center text-brand-muted text-sm">
              Loading heatmap…
            </div>
          )}
          <img
            src={url}
            alt="Activation heatmap"
            className={`w-full rounded-lg transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0'}`}
            onLoad={() => setLoaded(true)}
            onError={() => setErrored(true)}
          />
        </div>
      )}
    </div>
  )
}

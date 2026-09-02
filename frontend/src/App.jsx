import { useState, useEffect, useRef, useCallback } from 'react'
import Header from './components/Header'
import ScanForm from './components/ScanForm'
import StatusBanner from './components/StatusBanner'
import RiskBadge from './components/RiskBadge'
import SummaryTable from './components/SummaryTable'
import HeatmapPanel from './components/HeatmapPanel'
import LogPanel from './components/LogPanel'
import ModelInfoCard from './components/ModelInfoCard'
import { startScan, pollScan, saveBaseline, reportUrl } from './api'

const POLL_MS = 2000

export default function App() {
  const [job, setJob] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState('')
  const pollRef = useRef(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const startPolling = useCallback((jobId) => {
    stopPolling()
    pollRef.current = setInterval(async () => {
      try {
        const data = await pollScan(jobId)
        setJob(data)
        if (data.status === 'done' || data.status === 'error') {
          stopPolling()
          setScanning(false)
        }
      } catch {
        stopPolling()
        setScanning(false)
      }
    }, POLL_MS)
  }, [stopPolling])

  useEffect(() => () => stopPolling(), [stopPolling])

  async function handleScan(params) {
    setError('')
    setJob(null)
    setScanning(true)
    try {
      const data = await startScan(params)
      setJob(data)
      startPolling(data.job_id)
    } catch (err) {
      setError(err.message)
      setScanning(false)
    }
  }

  async function handleSaveBaseline() {
    if (!job?.job_id) return
    try {
      await saveBaseline(job.job_id)
      alert('Baseline saved successfully.')
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }

  const isDone = job?.status === 'done'
  const isError = job?.status === 'error'

  return (
    <div className="min-h-screen bg-brand-bg text-brand-text font-sans">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Scan form */}
        <ScanForm onScan={handleScan} scanning={scanning} />

        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg p-4 text-sm">
            {error}
          </div>
        )}

        {/* Progress / status */}
        {job && (
          <StatusBanner job={job} />
        )}

        {/* Risk + model info row */}
        {isDone && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-1">
              <RiskBadge score={job.overall_score} />
            </div>
            <div className="md:col-span-2">
              <ModelInfoCard info={job.model_info} />
            </div>
          </div>
        )}

        {/* Heatmap */}
        {isDone && job.heatmap_available && (
          <HeatmapPanel jobId={job.job_id} />
        )}

        {/* Summary table */}
        {isDone && job.summary?.length > 0 && (
          <SummaryTable rows={job.summary} />
        )}

        {/* Actions */}
        {isDone && (
          <div className="flex gap-3 flex-wrap">
            <a
              href={reportUrl(job.job_id)}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 bg-brand-accent hover:bg-orange-400 text-brand-bg font-semibold px-5 py-2.5 rounded-lg text-sm transition-colors"
            >
              ↓ Download PDF Report
            </a>
            <button
              onClick={handleSaveBaseline}
              className="inline-flex items-center gap-2 bg-brand-surface border border-brand-border hover:border-brand-accent text-brand-text px-5 py-2.5 rounded-lg text-sm transition-colors"
            >
              📐 Save as Baseline
            </button>
          </div>
        )}

        {/* Log */}
        {job?.log?.length > 0 && (
          <LogPanel lines={job.log} status={job.status} />
        )}

        {isError && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg p-4 text-sm">
            <strong>Scan failed:</strong> {job.error}
          </div>
        )}
      </main>
    </div>
  )
}

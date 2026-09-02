/**
 * NeuroFence API client
 */

const BASE = '/api'

export async function startScan({ modelPath, numPrompts = 200, scanLimit = 60 }) {
  const res = await fetch(`${BASE}/scan/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model_path: modelPath,
      num_prompts: numPrompts,
      scan_limit: scanLimit,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to start scan')
  }
  return res.json()
}

export async function pollScan(jobId) {
  const res = await fetch(`${BASE}/scan/${jobId}`)
  if (!res.ok) throw new Error('Failed to poll scan status')
  return res.json()
}

export function heatmapUrl(jobId) {
  return `${BASE}/scan/${jobId}/heatmap`
}

export function reportUrl(jobId) {
  return `${BASE}/scan/${jobId}/report`
}

export async function saveBaseline(jobId) {
  const res = await fetch(`${BASE}/baseline/save?job_id=${jobId}`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to save baseline')
  return res.json()
}

export async function healthCheck() {
  const res = await fetch(`${BASE}/health`)
  return res.ok
}

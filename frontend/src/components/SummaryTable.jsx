import { useState } from 'react'

const COLS = [
  { key: 'layer',         label: 'Layer',          numeric: false },
  { key: 'mean',          label: 'Mean',            numeric: true  },
  { key: 'std',           label: 'Std Dev',         numeric: true  },
  { key: 'max',           label: 'Max |Δ|',         numeric: true  },
  { key: 'energy',        label: 'Energy',          numeric: true  },
  { key: 'spike_score',   label: 'Spike',           numeric: true  },
  { key: 'anomaly_score', label: 'Anomaly Score',   numeric: true  },
  { key: 'flagged',       label: 'Flagged',         numeric: false },
]

const PAGE_SIZE = 20

function fmt(v, numeric) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'boolean') return v ? '⚑' : ''
  if (numeric) return typeof v === 'number' ? v.toFixed(4) : v
  return String(v)
}

export default function SummaryTable({ rows }) {
  const [page, setPage] = useState(0)
  const [sortKey, setSortKey] = useState('anomaly_score')
  const [sortAsc, setSortAsc] = useState(false)

  function toggleSort(key) {
    if (sortKey === key) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(false) }
    setPage(0)
  }

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey]
    if (av === bv) return 0
    const cmp = av < bv ? -1 : 1
    return sortAsc ? cmp : -cmp
  })

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const pageRows = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="bg-brand-surface border border-brand-border rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-brand-border flex items-center justify-between">
        <h3 className="text-sm font-semibold text-brand-text">
          Layer Anomaly Summary
          <span className="ml-2 text-brand-muted font-normal text-xs">
            ({rows.length} layers, {rows.filter(r => r.flagged).length} flagged)
          </span>
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-brand-bg border-b border-brand-border">
              {COLS.map(col => (
                <th
                  key={col.key}
                  onClick={() => toggleSort(col.key)}
                  className="px-3 py-2 text-left text-brand-muted font-semibold cursor-pointer hover:text-brand-text select-none whitespace-nowrap"
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span className="ml-1">{sortAsc ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr
                key={i}
                className={`border-b border-brand-border/50 ${
                  row.flagged
                    ? 'bg-red-900/20 hover:bg-red-900/30'
                    : i % 2 === 0
                    ? 'bg-transparent hover:bg-brand-bg/50'
                    : 'bg-brand-bg/30 hover:bg-brand-bg/50'
                }`}
              >
                {COLS.map(col => (
                  <td
                    key={col.key}
                    className={`px-3 py-1.5 font-mono whitespace-nowrap ${
                      col.key === 'flagged' && row.flagged
                        ? 'text-red-400 font-bold'
                        : col.key === 'anomaly_score'
                        ? 'text-brand-accent font-semibold'
                        : 'text-brand-text'
                    }`}
                  >
                    {fmt(row[col.key], col.numeric)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-brand-border text-xs text-brand-muted">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1 rounded border border-brand-border disabled:opacity-30 hover:border-brand-accent"
          >
            ← Prev
          </button>
          <span>Page {page + 1} / {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
            className="px-3 py-1 rounded border border-brand-border disabled:opacity-30 hover:border-brand-accent"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}

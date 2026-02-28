import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, AlertTriangle, Zap, TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import { formatINR, formatPct, categoryLabel, categoryIcon, categoryBadgeClass } from '../utils/formatters'
import { OverallScoreBadge, ScoreGrid } from './ScoreBar'
import ReturnsTable from './ReturnsTable'

export default function ResultCard({ product, rank, allocation, magicMode }) {
  const [expanded, setExpanded] = useState(rank === 1)

  const score    = product.scores?.overall ?? 0
  const catLabel = categoryLabel(product.category)
  const catIcon  = categoryIcon(product.category)

  const priceOrRate = product.current_rate
    ? `${product.current_rate.toFixed(2)}% p.a.`
    : product.current_price
      ? `₹${product.current_price.toFixed(2)}`
      : '—'

  const yieldStr = product.current_yield
    ? `${product.current_yield.toFixed(2)}% dist. yield`
    : null

  return (
    <div className={clsx(
      'card animate-slide-up border transition-all duration-200',
      rank === 1 && 'border-saffron/30 shadow-md shadow-saffron/10',
    )}>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start gap-4">
        {/* Rank badge */}
        <div className="flex-shrink-0 text-center">
          <div className={clsx(
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
            rank === 1 ? 'bg-saffron text-white' : 'bg-slate-100 text-slate-600'
          )}>
            {rank}
          </div>
        </div>

        {/* Product info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 flex-wrap">
            <span className={clsx('badge', categoryBadgeClass(product.category))}>
              {catIcon} {catLabel}
            </span>
            {rank === 1 && (
              <span className="badge bg-saffron/10 text-saffron">
                ⭐ Top Pick
              </span>
            )}
          </div>
          <h3 className="mt-1.5 font-bold text-slate-800 text-base leading-snug">
            {product.name}
          </h3>
          {product.issuer && (
            <p className="text-xs text-slate-400 mt-0.5">{product.issuer}</p>
          )}
        </div>

        {/* Score */}
        <div className="flex-shrink-0">
          <OverallScoreBadge score={score} size="sm" />
        </div>
      </div>

      {/* ── Key metrics strip ───────────────────────────────────────────── */}
      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Metric label="Rate / Price" value={priceOrRate} highlight />
        {yieldStr && <Metric label="Yield" value={yieldStr} />}
        <Metric label="1Y Return" value={formatPct(product.returns?.y1)} color={product.returns?.y1 >= 0 ? 'green' : 'red'} />
        <Metric label="Confidence" value={`${product.confidence}%`} />
        {magicMode && allocation && (
          <Metric
            label="AI Allocation"
            value={`${allocation.percentage}% (${formatINR(allocation.amount_inr)})`}
            highlight
          />
        )}
      </div>

      {/* ── Duration suitability ────────────────────────────────────────── */}
      <div className="mt-3 flex items-center gap-2 text-xs text-slate-600 bg-slate-50 rounded-lg px-3 py-2">
        <TrendingUp size={13} className="text-indgreen flex-shrink-0" />
        {product.duration_suitability}
      </div>

      {/* ── AI explanation (if available) ───────────────────────────────── */}
      {product.extra?.explanation && (
        <p className="mt-3 text-sm text-slate-600 leading-relaxed border-l-2 border-saffron/40 pl-3">
          {product.extra.explanation}
        </p>
      )}

      {/* ── Magic mode reasoning ────────────────────────────────────────── */}
      {magicMode && allocation?.reasoning && (
        <div className="mt-3 flex gap-2 bg-saffron/5 border border-saffron/20 rounded-lg p-3 text-sm text-slate-700">
          <Zap size={14} className="text-saffron flex-shrink-0 mt-0.5" />
          <span>{allocation.reasoning}</span>
        </div>
      )}

      {/* ── Expand toggle ───────────────────────────────────────────────── */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="mt-4 w-full flex items-center justify-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors py-1"
      >
        {expanded ? <><ChevronUp size={14} /> Less detail</> : <><ChevronDown size={14} /> More detail</>}
      </button>

      {/* ── Expanded section ────────────────────────────────────────────── */}
      {expanded && (
        <div className="mt-4 space-y-5 border-t border-slate-100 pt-4 animate-fade-in">

          {/* Returns table */}
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Historical Returns
            </h4>
            <ReturnsTable returns={product.returns} category={product.category} />
          </div>

          {/* Score breakdown */}
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Score Breakdown
            </h4>
            <ScoreGrid scores={product.scores} />
          </div>

          {/* Drivers + Risks */}
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Key Drivers
              </h4>
              <ul className="space-y-1.5">
                {product.key_drivers?.map((d, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                    <span className="text-green-500 font-bold flex-shrink-0">✓</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Risks
              </h4>
              <ul className="space-y-1.5">
                {product.risks?.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                    <AlertTriangle size={11} className="text-yellow-500 flex-shrink-0 mt-0.5" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Source links */}
          {product.source_links?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Data Sources
              </h4>
              <div className="flex flex-wrap gap-2">
                {product.source_links.map((link, i) => {
                  const host = (() => { try { return new URL(link).hostname.replace('www.', '') } catch { return link } })()
                  return (
                    <a
                      key={i}
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-slate-400 hover:text-indigo-600 transition-colors"
                    >
                      <ExternalLink size={10} />
                      {host}
                    </a>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Metric({ label, value, highlight, color }) {
  return (
    <div className="bg-slate-50 rounded-lg px-3 py-2">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={clsx(
        'text-sm font-bold mt-0.5',
        highlight  ? 'text-saffron' :
        color === 'green' ? 'text-green-600' :
        color === 'red'   ? 'text-red-500' :
        'text-slate-800'
      )}>
        {value}
      </div>
    </div>
  )
}

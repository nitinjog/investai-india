import clsx from 'clsx'

const scoreColor = (score) => {
  if (score >= 75) return { bar: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' }
  if (score >= 55) return { bar: 'bg-yellow-500', text: 'text-yellow-700', bg: 'bg-yellow-50' }
  return { bar: 'bg-red-500', text: 'text-red-600', bg: 'bg-red-50' }
}

export function ScoreBar({ label, score, showValue = true, className }) {
  const colors = scoreColor(score)
  return (
    <div className={clsx('space-y-1', className)}>
      {label && (
        <div className="flex justify-between text-xs text-slate-500">
          <span>{label}</span>
          {showValue && <span className={clsx('font-semibold', colors.text)}>{Math.round(score)}</span>}
        </div>
      )}
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-700', colors.bar)}
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
    </div>
  )
}

export function OverallScoreBadge({ score, size = 'md' }) {
  const colors = scoreColor(score)
  const sizes = {
    sm: 'w-10 h-10 text-sm',
    md: 'w-14 h-14 text-lg',
    lg: 'w-20 h-20 text-2xl',
  }
  return (
    <div className={clsx(
      'rounded-full flex flex-col items-center justify-center font-bold text-white shadow-md',
      sizes[size],
      colors.bar,
    )}>
      {Math.round(score)}
    </div>
  )
}

export function ScoreGrid({ scores }) {
  const items = [
    { key: 'performance', label: 'Performance' },
    { key: 'trend',       label: 'Trend' },
    { key: 'macro',       label: 'Macro' },
    { key: 'sentiment',   label: 'Sentiment' },
    { key: 'yield_score', label: 'Yield' },
    { key: 'stability',   label: 'Stability' },
    { key: 'liquidity',   label: 'Liquidity' },
    { key: 'duration_fit',label: 'Duration Fit' },
  ]
  return (
    <div className="space-y-2">
      {items.map(({ key, label }) => (
        <ScoreBar key={key} label={label} score={scores[key] || 0} />
      ))}
    </div>
  )
}

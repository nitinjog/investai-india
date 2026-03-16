import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowLeft, RefreshCw, Sparkles, TrendingUp, AlertCircle, Wifi, WifiOff } from 'lucide-react'
import { useRecommendations } from '../hooks/useRecommendations'
import ResultCard from '../components/ResultCard'
import LoadingState from '../components/LoadingState'
import { formatINR, formatPct } from '../utils/formatters'

function MacroPill({ label, value }) {
  if (value == null) return null
  return (
    <div className="bg-white border border-slate-100 rounded-xl px-3 py-2 text-center">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="text-sm font-bold text-slate-800 mt-0.5">{value}</div>
    </div>
  )
}

export default function Results() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const params    = location.state?.params

  const { data, loading, error, fetch: fetchRecs } = useRecommendations()

  useEffect(() => {
    if (!params) { navigate('/'); return }
    fetchRecs(params)
  }, [])  // eslint-disable-line

  if (!params) return null

  if (loading) return (
    <main className="max-w-2xl mx-auto px-4 py-10">
      <LoadingState magicMode={params?.magicMode} />
    </main>
  )

  if (error) return (
    <main className="max-w-2xl mx-auto px-4 py-20 text-center space-y-4">
      <AlertCircle size={48} className="text-red-400 mx-auto" />
      <h2 className="text-xl font-bold text-slate-800">Analysis Failed</h2>
      <p className="text-slate-500 text-sm">{error}</p>
      <button onClick={() => navigate('/')} className="btn-primary">
        Try Again
      </button>
    </main>
  )

  if (!data) return null

  const { recommendations = [], macro_context, magic_allocation, duration_label, amount,
          data_quality, price_data_as_of } = data

  // Build allocation map from magic mode
  const allocMap = magic_allocation
    ? Object.fromEntries(
        (magic_allocation.allocation || []).map(a => [a.product_id, a])
      )
    : {}

  return (
    <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* ── Back + refresh ──────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition"
        >
          <ArrowLeft size={16} />
          New search
        </button>
        <button
          onClick={() => fetchRecs(params)}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* ── Summary header ──────────────────────────────────────────────── */}
      <div className="card shadow-sm space-y-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800">
            Top 5 Recommendations
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            For <span className="font-semibold text-saffron">{formatINR(amount)}</span> over{' '}
            <span className="font-semibold">{duration_label}</span>
          </p>
        </div>

        {/* Macro strip */}
        {macro_context && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <MacroPill label="RBI Repo Rate" value={macro_context.rbi_repo_rate ? `${macro_context.rbi_repo_rate}%` : null} />
            <MacroPill label="CPI Inflation"  value={macro_context.cpi_inflation  ? `${macro_context.cpi_inflation}%`  : null} />
            <MacroPill label="USD/INR"         value={macro_context.usd_inr        ? `₹${macro_context.usd_inr}`        : null} />
            <MacroPill label="Gold (10g)"      value={macro_context.gold_price_inr ? `₹${macro_context.gold_price_inr?.toLocaleString('en-IN')}` : null} />
          </div>
        )}
      </div>

      {/* ── Magic allocation card ────────────────────────────────────────── */}
      {params.magicMode && magic_allocation && (
        <div className="card border-saffron/20 bg-gradient-to-r from-saffron/5 to-white space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-saffron" />
            <h2 className="font-bold text-slate-800">AI Allocation Strategy</h2>
            <span className="ml-auto badge bg-saffron/10 text-saffron text-xs">
              Confidence: {magic_allocation.confidence}%
            </span>
          </div>

          <p className="text-sm text-slate-700 leading-relaxed">
            {magic_allocation.overall_reasoning}
          </p>

          <div className="flex items-center gap-4 text-sm">
            <div>
              <span className="text-slate-500">Expected return:</span>{' '}
              <span className="font-semibold text-green-600">
                {magic_allocation.expected_return_min}% – {magic_allocation.expected_return_max}%
              </span>
            </div>
          </div>

          {magic_allocation.risks?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {magic_allocation.risks.map((r, i) => (
                <span key={i} className="text-xs bg-yellow-50 text-yellow-700 border border-yellow-100 rounded-full px-2.5 py-0.5">
                  ⚠ {r}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Data quality banner ──────────────────────────────────────────── */}
      {data_quality === 'live' && (
        <div className="flex items-center gap-2 text-xs text-green-700 bg-green-50 border border-green-100 rounded-xl px-4 py-2.5">
          <Wifi size={13} className="flex-shrink-0" />
          <span>
            <strong>Live market data</strong>
            {price_data_as_of ? ` · Prices as of ${price_data_as_of}` : ''}
            {' · ETF prices via AMFI / NSE'}
          </span>
        </div>
      )}
      {data_quality === 'partial' && (
        <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-xl px-4 py-2.5">
          <Wifi size={13} className="flex-shrink-0" />
          <span>
            <strong>Partial live data</strong>
            {price_data_as_of ? ` · Most prices as of ${price_data_as_of}` : ''}
            {' · Some prices are estimated (Est. badge)'}
          </span>
        </div>
      )}
      {data_quality === 'mock' && (
        <div className="flex items-center gap-2 text-xs text-orange-700 bg-orange-50 border border-orange-200 rounded-xl px-4 py-2.5">
          <WifiOff size={13} className="flex-shrink-0" />
          <span>
            <strong>Estimated prices</strong>
            {' · Live feed temporarily unavailable · Scores use approximate Mar 2026 values · Refresh to retry'}
          </span>
        </div>
      )}

      {/* ── Result cards ─────────────────────────────────────────────────── */}
      <div className="space-y-4">
        {recommendations.map((product, i) => (
          <ResultCard
            key={product.id}
            product={product}
            rank={i + 1}
            allocation={allocMap[product.id]}
            magicMode={params.magicMode}
          />
        ))}
      </div>

      {/* ── Data sources ─────────────────────────────────────────────────── */}
      {data.data_sources?.length > 0 && (
        <div className="text-center text-xs text-slate-400 space-y-1">
          <div>Data sources: {data.data_sources.join(' · ')}</div>
          <div>
            Analysis at: {new Date(data.analysis_timestamp).toLocaleTimeString('en-IN')}
            {price_data_as_of ? ` · Prices as of: ${price_data_as_of}` : ''}
            {' · FD rates as of 15-Mar-2026'}
          </div>
          <div className="mt-2 text-slate-300">
            ⚠ Not SEBI-registered advice. For informational purposes only.
          </div>
        </div>
      )}
    </main>
  )
}

import { useNavigate } from 'react-router-dom'
import { TrendingUp, Shield, Zap, BarChart3 } from 'lucide-react'
import InvestForm from '../components/InvestForm'
import LoadingState from '../components/LoadingState'
import { useRecommendations } from '../hooks/useRecommendations'

const ASSET_CLASSES = [
  { icon: '🏦', label: 'Fixed Deposits',   sub: '13 banks & NBFCs' },
  { icon: '🥇', label: 'Gold ETFs',        sub: 'NSE listed, AMFI NAV' },
  { icon: '📈', label: 'Nifty ETFs',       sub: 'Broad market index' },
  { icon: '🏭', label: 'Sector ETFs',      sub: 'Banking, IT, Pharma…' },
  { icon: '📋', label: 'Bonds / NCDs',     sub: 'NSE debt segment' },
  { icon: '🏢', label: 'REITs',            sub: 'Embassy, Mindspace…' },
  { icon: '⚡', label: 'InvITs',           sub: 'IndiGrid, PowerGrid…' },
]

const FEATURES = [
  { icon: BarChart3, title: 'Quantitative Scoring',  desc: '8-factor composite score per product — performance, trend, macro, sentiment, yield, stability, liquidity, duration' },
  { icon: Shield,    title: 'India-First Data',       desc: 'NSE, AMFI, RBI DBIE, IBJA gold rates, GDELT news, Economic Times RSS — all India-specific sources' },
  { icon: Zap,       title: 'Magic AI Mode',          desc: 'Gemini AI autonomously allocates your money across top products and explains its reasoning in plain Hindi/English' },
  { icon: TrendingUp,title: '7 Asset Classes',        desc: 'FDs, Gold ETFs, Silver ETFs, Nifty ETFs, Sector ETFs, Listed REITs, InvITs — all in one place' },
]

export default function Home() {
  const navigate = useNavigate()
  const { data, loading, error, fetch: fetchRecs } = useRecommendations()

  const handleSubmit = async (params) => {
    const result = await fetchRecs(params)
    // Navigate after fetch resolves (data set via hook)
    navigate('/results', { state: { params } })
  }

  // If loading show overlay
  if (loading) {
    return (
      <main className="max-w-2xl mx-auto px-4 py-10">
        <LoadingState magicMode={false} />
      </main>
    )
  }

  return (
    <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-16">
      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="text-center space-y-5">
        <div className="inline-flex items-center gap-2 bg-saffron/10 text-saffron rounded-full px-4 py-1.5 text-sm font-semibold">
          <span className="w-2 h-2 rounded-full bg-saffron animate-pulse" />
          Live Indian Market Analysis
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 leading-tight">
          Daily Investment Advisor<br />
          <span className="text-saffron">— India</span>
        </h1>
        <p className="text-slate-500 text-lg max-w-2xl mx-auto leading-relaxed">
          Enter your amount and horizon. Our engine analyses 40+ investment products across 7 Indian asset classes — then ranks the best 5 for you, powered by real market data.
        </p>
      </section>

      {/* ── Form + Asset pills ─────────────────────────────────────────── */}
      <div className="grid lg:grid-cols-2 gap-10 items-start">
        <div className="card shadow-lg">
          <InvestForm onSubmit={handleSubmit} loading={loading} />
        </div>

        <div className="space-y-6">
          {/* Asset classes */}
          <div>
            <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">
              Asset Classes Covered
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {ASSET_CLASSES.map(a => (
                <div key={a.label} className="flex items-center gap-3 bg-white rounded-xl border border-slate-100 px-4 py-3">
                  <span className="text-2xl">{a.icon}</span>
                  <div>
                    <div className="text-sm font-semibold text-slate-800">{a.label}</div>
                    <div className="text-xs text-slate-400">{a.sub}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="space-y-3">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex gap-3">
                <div className="w-9 h-9 rounded-xl bg-slate-50 flex items-center justify-center flex-shrink-0">
                  <Icon size={16} className="text-saffron" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-700">{title}</div>
                  <div className="text-xs text-slate-500 leading-relaxed">{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Disclaimer + Developer credit ───────────────────────────────── */}
      <div className="text-center text-xs text-slate-400 border-t border-slate-100 pt-8 pb-4 space-y-2">
        <p>⚠️ For informational purposes only. Not SEBI-registered investment advice. Please consult a financial advisor before investing.
        Data sourced from NSE, AMFI, RBI DBIE, IBJA, GDELT. Prices refreshed every 15 minutes.</p>
        <p>developed by &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Nitin Nandrajog</p>
      </div>
    </main>
  )
}

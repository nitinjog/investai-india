import { TrendingUp, BarChart3, Brain, Database } from 'lucide-react'

const steps = [
  { icon: Database,   label: 'Fetching live market data from NSE, AMFI, RBI…' },
  { icon: BarChart3,  label: 'Computing performance & trend scores…' },
  { icon: TrendingUp, label: 'Analysing macro environment & sentiment…' },
  { icon: Brain,      label: 'Ranking investments for your profile…' },
]

export default function LoadingState({ magicMode }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-8">
      {/* Spinner */}
      <div className="relative">
        <div className="w-20 h-20 rounded-full border-4 border-slate-200 border-t-saffron animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <TrendingUp size={24} className="text-saffron" />
        </div>
      </div>

      {/* Headline */}
      <div className="text-center space-y-1.5">
        <h2 className="text-xl font-bold text-slate-800">
          {magicMode ? '✨ Magic Investment Mode Active' : 'Analysing Indian Markets…'}
        </h2>
        <p className="text-slate-500 text-sm max-w-sm">
          {magicMode
            ? 'Gemini AI is crafting your personalised allocation strategy'
            : 'Scanning 40+ products across 7 asset classes in real-time'}
        </p>
      </div>

      {/* Steps */}
      <div className="space-y-3 w-full max-w-sm">
        {steps.map(({ icon: Icon, label }, i) => (
          <div
            key={i}
            className="flex items-center gap-3 text-sm text-slate-500 animate-pulse-slow"
            style={{ animationDelay: `${i * 0.5}s` }}
          >
            <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0">
              <Icon size={14} className="text-saffron" />
            </div>
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}

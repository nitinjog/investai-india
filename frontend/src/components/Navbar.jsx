import { Link } from 'react-router-dom'
import { TrendingUp } from 'lucide-react'

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-saffron to-saffron-dark flex items-center justify-center shadow-sm">
            <TrendingUp size={18} className="text-white" />
          </div>
          <div className="leading-tight">
            <div className="font-bold text-slate-800 text-sm">InvestAI</div>
            <div className="text-xs text-slate-500 font-medium">India</div>
          </div>
        </Link>

        <div className="flex items-center gap-3 text-sm">
          <span className="hidden sm:flex items-center gap-1.5 text-slate-500">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            Live market data
          </span>
          <a
            href="https://www.nseindia.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-slate-600 transition-colors text-xs"
          >
            NSE
          </a>
          <a
            href="https://www.amfiindia.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-slate-600 transition-colors text-xs"
          >
            AMFI
          </a>
        </div>
      </div>
    </nav>
  )
}

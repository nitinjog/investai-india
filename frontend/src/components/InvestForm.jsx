import { useState } from 'react'
import { IndianRupee, Clock, Shield, Zap } from 'lucide-react'
import clsx from 'clsx'
import MagicToggle from './MagicToggle'

const DURATION_PRESETS = [
  { label: '7D',   value: 7,   unit: 'days'   },
  { label: '1M',   value: 1,   unit: 'months' },
  { label: '3M',   value: 3,   unit: 'months' },
  { label: '6M',   value: 6,   unit: 'months' },
  { label: '1Y',   value: 1,   unit: 'years'  },
  { label: '3Y',   value: 3,   unit: 'years'  },
  { label: '5Y',   value: 5,   unit: 'years'  },
]

const AMOUNT_PRESETS = [5000, 10000, 50000, 100000, 500000, 1000000]

const RISK_OPTIONS = [
  { value: 'low',    label: 'Conservative',  icon: Shield,  desc: 'FDs, bonds, gold'           },
  { value: 'medium', label: 'Balanced',      icon: Clock,   desc: 'Mix of equity & debt'        },
  { value: 'high',   label: 'Aggressive',    icon: Zap,     desc: 'Equity ETFs, REITs, InvITs' },
]

export default function InvestForm({ onSubmit, loading }) {
  const [amount, setAmount]           = useState('')
  const [durationValue, setDurVal]   = useState(1)
  const [durationUnit, setDurUnit]   = useState('years')
  const [magicMode, setMagicMode]    = useState(false)
  const [riskAppetite, setRisk]      = useState('medium')
  const [activePreset, setPreset]    = useState('1Y')

  const handlePreset = (preset) => {
    setDurVal(preset.value)
    setDurUnit(preset.unit)
    setPreset(preset.label)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const amt = parseFloat(amount)
    if (!amt || amt < 100) return
    onSubmit({ amount: amt, durationValue, durationUnit, magicMode, riskAppetite })
  }

  const formatAmountInput = (val) => {
    const num = parseFloat(val)
    if (!num) return ''
    if (num >= 10000000) return `${(num/10000000).toFixed(1)} Crore`
    if (num >= 100000)   return `${(num/100000).toFixed(1)} Lakh`
    return ''
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* ── Amount ──────────────────────────────────────────────────────── */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-slate-700">
          Investment Amount
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <IndianRupee size={18} className="text-slate-400" />
          </div>
          <input
            type="number"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            placeholder="10,000"
            min={100}
            className="w-full pl-10 pr-4 py-3.5 rounded-xl border border-slate-200 text-slate-800 text-lg font-semibold
                       focus:outline-none focus:ring-2 focus:ring-saffron/40 focus:border-saffron transition"
            required
          />
        </div>
        {amount && (
          <p className="text-xs text-slate-400 pl-1">
            ₹{parseFloat(amount).toLocaleString('en-IN')}
            {formatAmountInput(amount) && ` (${formatAmountInput(amount)})`}
          </p>
        )}
        {/* Amount presets */}
        <div className="flex flex-wrap gap-2 pt-1">
          {AMOUNT_PRESETS.map(a => (
            <button
              key={a}
              type="button"
              onClick={() => setAmount(String(a))}
              className="text-xs px-3 py-1 rounded-lg border border-slate-200 text-slate-600 hover:border-saffron hover:text-saffron transition"
            >
              ₹{a >= 100000 ? `${a/100000}L` : a >= 1000 ? `${a/1000}K` : a}
            </button>
          ))}
        </div>
      </div>

      {/* ── Duration ────────────────────────────────────────────────────── */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-slate-700">
          Investment Duration
        </label>
        {/* Presets */}
        <div className="flex flex-wrap gap-2">
          {DURATION_PRESETS.map(p => (
            <button
              key={p.label}
              type="button"
              onClick={() => handlePreset(p)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-sm font-medium border transition',
                activePreset === p.label
                  ? 'bg-saffron text-white border-saffron'
                  : 'bg-white border-slate-200 text-slate-600 hover:border-saffron hover:text-saffron'
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
        {/* Custom input */}
        <div className="flex gap-2">
          <input
            type="number"
            value={durationValue}
            onChange={e => { setDurVal(Number(e.target.value)); setPreset('') }}
            min={1}
            className="w-24 px-3 py-2.5 rounded-xl border border-slate-200 text-slate-800 font-semibold
                       focus:outline-none focus:ring-2 focus:ring-saffron/40 focus:border-saffron text-center"
          />
          <select
            value={durationUnit}
            onChange={e => { setDurUnit(e.target.value); setPreset('') }}
            className="flex-1 px-3 py-2.5 rounded-xl border border-slate-200 text-slate-700
                       focus:outline-none focus:ring-2 focus:ring-saffron/40 focus:border-saffron"
          >
            <option value="days">Days</option>
            <option value="months">Months</option>
            <option value="years">Years</option>
          </select>
        </div>
      </div>

      {/* ── Risk appetite ────────────────────────────────────────────────── */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-slate-700">
          Risk Appetite
        </label>
        <div className="grid grid-cols-3 gap-2">
          {RISK_OPTIONS.map(({ value, label, icon: Icon, desc }) => (
            <button
              key={value}
              type="button"
              onClick={() => setRisk(value)}
              className={clsx(
                'flex flex-col items-center gap-1.5 p-3 rounded-xl border text-center transition',
                riskAppetite === value
                  ? 'border-saffron bg-saffron/5'
                  : 'border-slate-200 hover:border-slate-300'
              )}
            >
              <Icon size={16} className={riskAppetite === value ? 'text-saffron' : 'text-slate-400'} />
              <span className={clsx('text-xs font-semibold', riskAppetite === value ? 'text-saffron' : 'text-slate-700')}>
                {label}
              </span>
              <span className="text-[10px] text-slate-400 leading-tight">{desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Magic mode ──────────────────────────────────────────────────── */}
      <MagicToggle enabled={magicMode} onChange={setMagicMode} />

      {/* ── Submit ──────────────────────────────────────────────────────── */}
      <button
        type="submit"
        disabled={loading || !amount}
        className="btn-primary w-full text-base flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Analysing…
          </>
        ) : (
          <>
            {magicMode ? '✨ Find Best Investments with AI' : '🔍 Find Best Investments'}
          </>
        )}
      </button>

      <p className="text-xs text-slate-400 text-center">
        Data from NSE · AMFI · RBI · IBJA · GDELT — refreshed every 15 min
      </p>
    </form>
  )
}

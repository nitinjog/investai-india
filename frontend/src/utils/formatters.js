export const formatINR = (amount) => {
  if (amount == null) return '—'
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(2)} Cr`
  if (amount >= 100_000)    return `₹${(amount / 100_000).toFixed(2)} L`
  if (amount >= 1_000)      return `₹${(amount / 1_000).toFixed(1)} K`
  return `₹${amount.toFixed(0)}`
}

export const formatPct = (val, decimals = 2) => {
  if (val == null) return '—'
  const sign = val >= 0 ? '+' : ''
  return `${sign}${val.toFixed(decimals)}%`
}

export const formatScore = (val) => {
  if (val == null) return '—'
  return Math.round(val)
}

export const scoreColor = (score) => {
  if (score >= 75) return 'text-green-600'
  if (score >= 55) return 'text-yellow-600'
  return 'text-red-500'
}

export const scoreBg = (score) => {
  if (score >= 75) return 'bg-green-500'
  if (score >= 55) return 'bg-yellow-500'
  return 'bg-red-500'
}

export const returnColor = (val) => {
  if (val == null) return 'text-gray-400'
  if (val > 0) return 'text-green-600'
  if (val < 0) return 'text-red-500'
  return 'text-gray-500'
}

export const categoryLabel = (cat) => {
  const map = {
    fd:         'Fixed Deposit',
    gold_etf:   'Gold ETF',
    silver_etf: 'Silver ETF',
    nifty_etf:  'Nifty ETF',
    sector_etf: 'Sector ETF',
    bond:       'Bond / NCD',
    reit:       'REIT',
    invit:      'InvIT',
  }
  return map[cat] || cat
}

export const categoryIcon = (cat) => {
  const map = {
    fd:         '🏦',
    gold_etf:   '🥇',
    silver_etf: '🥈',
    nifty_etf:  '📈',
    sector_etf: '🏭',
    bond:       '📋',
    reit:       '🏢',
    invit:      '⚡',
  }
  return map[cat] || '💼'
}

export const categoryBadgeClass = (cat) => {
  const map = {
    fd:         'bg-blue-100 text-blue-800',
    gold_etf:   'bg-yellow-100 text-yellow-800',
    silver_etf: 'bg-gray-100 text-gray-700',
    nifty_etf:  'bg-green-100 text-green-800',
    sector_etf: 'bg-purple-100 text-purple-800',
    bond:       'bg-indigo-100 text-indigo-800',
    reit:       'bg-orange-100 text-orange-800',
    invit:      'bg-teal-100 text-teal-800',
  }
  return map[cat] || 'bg-gray-100 text-gray-700'
}

import { formatPct, returnColor } from '../utils/formatters'
import clsx from 'clsx'

const PERIODS = [
  { key: 'd1', label: '1D'  },
  { key: 'w1', label: '1W'  },
  { key: 'm1', label: '1M'  },
  { key: 'm3', label: '3M'  },
  { key: 'm6', label: '6M'  },
  { key: 'y1', label: '1Y'  },
]

export default function ReturnsTable({ returns, category }) {
  const isFD = category === 'fd'

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            {PERIODS.map(p => (
              <th key={p.key} className="text-center text-slate-400 font-medium pb-1.5 px-1">
                {p.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            {PERIODS.map(p => {
              const val = returns?.[p.key]
              return (
                <td key={p.key} className="text-center px-1">
                  {val != null ? (
                    <span className={clsx('font-semibold', returnColor(val))}>
                      {formatPct(val, 1)}
                    </span>
                  ) : (
                    <span className="text-slate-300">—</span>
                  )}
                </td>
              )
            })}
          </tr>
        </tbody>
      </table>
    </div>
  )
}

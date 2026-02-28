import { Sparkles } from 'lucide-react'
import clsx from 'clsx'

export default function MagicToggle({ enabled, onChange }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      className={clsx(
        'w-full flex items-center gap-3 p-4 rounded-xl border-2 transition-all duration-200',
        enabled
          ? 'border-saffron bg-saffron/5 shadow-sm'
          : 'border-slate-200 bg-white hover:border-slate-300'
      )}
    >
      {/* Toggle switch */}
      <div className={clsx(
        'relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0',
        enabled ? 'bg-saffron' : 'bg-slate-300'
      )}>
        <span className={clsx(
          'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200',
          enabled ? 'translate-x-5' : 'translate-x-0'
        )} />
      </div>

      {/* Label */}
      <div className="flex-1 text-left">
        <div className="flex items-center gap-1.5">
          <Sparkles size={15} className={enabled ? 'text-saffron' : 'text-slate-400'} />
          <span className={clsx('text-sm font-semibold', enabled ? 'text-saffron' : 'text-slate-700')}>
            Magic Investment Mode
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-0.5">
          {enabled
            ? 'AI will autonomously allocate your funds and explain its reasoning'
            : 'Let Gemini AI decide the optimal allocation strategy for you'}
        </p>
      </div>
    </button>
  )
}

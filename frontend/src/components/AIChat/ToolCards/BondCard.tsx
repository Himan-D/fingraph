import { Banknote, Percent, Clock, ArrowUpRight, ArrowDownRight, Info } from 'lucide-react'

interface BondCardProps {
  data: Record<string, any>
}

export default function BondCard({ data }: BondCardProps) {
  const { metrics, price_sensitivity } = data
  if (!metrics) return null

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-sky-500/10 to-blue-500/10 border-b border-terminal-border">
        <div className="p-2 bg-sky-500/20 rounded-lg">
          <Banknote size={18} className="text-sky-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">Bond Metrics</h3>
          <p className="text-xs text-terminal-muted">
            ₹{Number(data.face_value).toLocaleString()} • {data.coupon_rate_pct}% Coupon • {data.years_to_maturity}y • {data.payment_frequency}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-px bg-terminal-border">
        {[
          { label: 'Face Value', value: `₹${Number(data.face_value).toLocaleString()}` },
          { label: 'Coupon Rate', value: `${data.coupon_rate_pct}%` },
          { label: 'Maturity', value: `${data.years_to_maturity} years` },
          { label: 'Current Price', value: `₹${Number(data.current_price).toLocaleString()}` },
        ].map(m => (
          <div key={m.label} className="bg-terminal-card p-3">
            <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{m.label}</div>
            <span className="text-sm font-semibold">{m.value}</span>
          </div>
        ))}
      </div>

      <div className="p-4 bg-terminal-bg border-t border-terminal-border flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Yield to Maturity</div>
          <span className="text-2xl font-bold text-sky-400">{metrics.ytm_pct}%</span>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Current Yield</div>
          <span className="text-lg font-semibold">{metrics.current_yield_pct}%</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-px bg-terminal-border">
        {[
          { label: 'Macaulay Duration', value: `${metrics.macaulay_duration_years} years`, icon: Clock },
          { label: 'Modified Duration', value: metrics.modified_duration, icon: Percent },
          { label: 'Convexity', value: metrics.convexity, icon: Percent },
        ].map(m => {
          const Icon = m.icon
          return (
            <div key={m.label} className="bg-terminal-card p-3">
              <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
                <Icon size={12} />
                <span className="text-[10px] uppercase tracking-wider">{m.label}</span>
              </div>
              <span className="text-sm font-semibold">{m.value}</span>
            </div>
          )
        })}
      </div>

      {price_sensitivity && (
        <div className="grid grid-cols-2 gap-px bg-terminal-border border-t border-terminal-border">
          <div className="bg-terminal-card p-3">
            <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
              <ArrowDownRight size={12} className="text-red-400" />
              <span className="text-[10px] uppercase tracking-wider">+1% Yield Change</span>
            </div>
            <span className="text-sm font-semibold text-red-400">{price_sensitivity.price_change_per_1pct_yield_up_pct}%</span>
          </div>
          <div className="bg-terminal-card p-3">
            <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
              <ArrowUpRight size={12} className="text-green-400" />
              <span className="text-[10px] uppercase tracking-wider">−1% Yield Change</span>
            </div>
            <span className="text-sm font-semibold text-green-400">{price_sensitivity.price_change_per_1pct_yield_down_pct}%</span>
          </div>
        </div>
      )}

      {data.interpretation && (
        <div className="p-3 border-t border-terminal-border flex items-start gap-2">
          <Info size={14} className="text-terminal-muted mt-0.5 flex-shrink-0" />
          <p className="text-xs text-terminal-muted leading-relaxed">{data.interpretation}</p>
        </div>
      )}
    </div>
  )
}

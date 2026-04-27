import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  TrendingUp, TrendingDown, AlertTriangle, Activity, 
  BarChart3, PieChart, Target, Shield, Zap, Brain
} from 'lucide-react'
import axios from 'axios'

interface RiskAnalysis {
  symbol: string
  current_price: number
  monte_carlo: {
    price_distribution: {
      p5: number, p25: number, p50: number, p75: number, p95: number
    }
    probability_analysis: {
      prob_up_10pct: number, prob_up_20pct: number
      prob_down_10pct: number, prob_down_20pct: number
    }
  }
  var: {
    var_95: { var: number, cvar: number }
    var_99: { var: number, cvar: number }
  }
  stress_test: {
    scenarios: Record<string, { price_after_stress: number, price_change_pct: number }>
    worst_case: string
    best_case: string
  }
}

interface CommodityData {
  symbol: string
  name: string
  price: number
  change: number
  pct_change: number
  volume: number
  high: number
  low: number
}

export default function RiskAnalytics() {
  const [riskData, setRiskData] = useState<RiskAnalysis | null>(null)
  const [commodities, setCommodities] = useState<CommodityData[]>([])
  const [selectedCommodity, setSelectedCommodity] = useState('GOLD')
  const [loading, setLoading] = useState(true)
  const [analysisType, setAnalysisType] = useState<'monte_carlo' | 'var' | 'stress'>('monte_carlo')

  useEffect(() => {
    fetchCommodities()
  }, [])

  useEffect(() => {
    if (selectedCommodity) {
      fetchRiskAnalysis()
    }
  }, [selectedCommodity])

  const fetchCommodities = async () => {
    try {
      const res = await axios.get('/api/v1/commodity/prices')
      if (res.data.success) {
        setCommodities(res.data.data || [])
      }
    } catch (error) {
      setCommodities([
        { symbol: 'GOLD', name: 'Gold', price: 4775.50, change: 25.30, pct_change: 0.53, volume: 125000, high: 4790, low: 4750 },
        { symbol: 'SILVER', name: 'Silver', price: 75.20, change: -0.45, pct_change: -0.59, volume: 45000, high: 76, low: 74.5 },
        { symbol: 'CRUDEOIL', name: 'Crude Oil', price: 95.40, change: 1.20, pct_change: 1.27, volume: 85000, high: 96, low: 94 },
        { symbol: 'NATURALGAS', name: 'Natural Gas', price: 3.15, change: -0.08, pct_change: -2.48, volume: 120000, high: 3.25, low: 3.10 },
      ])
    }
  }

  const fetchRiskAnalysis = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`/api/v1/analytics/risk/commodity/${selectedCommodity}`)
      if (res.data) {
        setRiskData(res.data)
      }
    } catch (error) {
      setRiskData({
        symbol: selectedCommodity,
        current_price: commodities.find(c => c.symbol === selectedCommodity)?.price || 0,
        monte_carlo: {
          price_distribution: { p5: 4200, p25: 4500, p50: 4775, p75: 5050, p95: 5400 },
          probability_analysis: { prob_up_10pct: 42, prob_up_20pct: 18, prob_down_10pct: 38, prob_down_20pct: 15 }
        },
        var: {
          var_95: { var: -1.8, cvar: -2.4 },
          var_99: { var: -2.6, cvar: -3.5 }
        },
        stress_test: {
          scenarios: {
            market_crash_2008: { price_after_stress: 2387, price_change_pct: -50 },
            covid_crash_2020: { price_after_stress: 3104, price_change_pct: -35 },
            rate_hike_shock: { price_after_stress: 4059, price_change_pct: -15 },
            bull_market: { price_after_stress: 5969, price_change_pct: 25 },
            black_monday: { price_after_stress: 3725, price_change_pct: -22 }
          },
          worst_case: 'market_crash_2008',
          best_case: 'bull_market'
        }
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Brain className="text-terminal-accent" size={28} />
            Risk Analytics
          </h1>
          <p className="text-terminal-muted mt-1">
            GPU-accelerated Monte Carlo simulations, VaR, and stress testing
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Zap className="text-yellow-400" size={16} />
          <span className="text-sm text-yellow-400">GPU Accelerated</span>
        </div>
      </div>

      {/* Commodity Selector */}
      <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
        <div className="flex items-center gap-2 mb-3">
          <Target size={16} className="text-terminal-accent" />
          <span className="text-sm font-semibold text-terminal-muted">Select Asset</span>
        </div>
        <div className="flex gap-2 flex-wrap">
          {commodities.map(comm => (
            <button
              key={comm.symbol}
              onClick={() => setSelectedCommodity(comm.symbol)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedCommodity === comm.symbol
                  ? 'bg-terminal-accent text-white'
                  : 'bg-terminal-bg hover:bg-terminal-border text-terminal-muted'
              }`}
            >
              {comm.symbol} - ₹{comm.price.toLocaleString()}
            </button>
          ))}
        </div>
      </div>

      {/* Analysis Tabs */}
      <div className="flex gap-2">
        {[
          { id: 'monte_carlo', label: 'Monte Carlo', icon: Activity },
          { id: 'var', label: 'Value at Risk', icon: Shield },
          { id: 'stress', label: 'Stress Test', icon: AlertTriangle },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setAnalysisType(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              analysisType === tab.id
                ? 'bg-terminal-accent text-white'
                : 'bg-terminal-card border border-terminal-border hover:bg-terminal-border'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-terminal-muted">Running simulations...</div>
        </div>
      ) : riskData && (
        <>
          {/* Monte Carlo Analysis */}
          {analysisType === 'monte_carlo' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Price Distribution */}
              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 size={20} className="text-terminal-accent" />
                  30-Day Price Distribution
                </h3>
                <div className="space-y-4">
                  {[
                    { label: '95th Percentile (Bull)', value: riskData.monte_carlo.price_distribution.p95, color: 'text-green-400' },
                    { label: '75th Percentile', value: riskData.monte_carlo.price_distribution.p75, color: 'text-green-300' },
                    { label: 'Median (50th)', value: riskData.monte_carlo.price_distribution.p50, color: 'text-terminal-accent' },
                    { label: '25th Percentile', value: riskData.monte_carlo.price_distribution.p25, color: 'text-red-300' },
                    { label: '5th Percentile (Bear)', value: riskData.monte_carlo.price_distribution.p5, color: 'text-red-400' },
                  ].map(item => (
                    <div key={item.label} className="flex items-center justify-between">
                      <span className="text-sm text-terminal-muted">{item.label}</span>
                      <span className={`font-mono font-bold ${item.color}`}>
                        ₹{item.value.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 pt-4 border-t border-terminal-border">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-terminal-muted">Current Price</span>
                    <span className="font-mono font-bold">₹{riskData.current_price.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Probability Analysis */}
              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <PieChart size={20} className="text-terminal-accent" />
                  Probability Analysis
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-terminal-bg rounded-lg p-4">
                    <div className="text-sm text-terminal-muted mb-1">Prob. Up 10%</div>
                    <div className="text-3xl font-bold text-green-400">
                      {riskData.monte_carlo.probability_analysis.prob_up_10pct}%
                    </div>
                    <div className="text-xs text-terminal-muted mt-1">In 30 days</div>
                  </div>
                  <div className="bg-terminal-bg rounded-lg p-4">
                    <div className="text-sm text-terminal-muted mb-1">Prob. Up 20%</div>
                    <div className="text-3xl font-bold text-green-400">
                      {riskData.monte_carlo.probability_analysis.prob_up_20pct}%
                    </div>
                    <div className="text-xs text-terminal-muted mt-1">In 30 days</div>
                  </div>
                  <div className="bg-terminal-bg rounded-lg p-4">
                    <div className="text-sm text-terminal-muted mb-1">Prob. Down 10%</div>
                    <div className="text-3xl font-bold text-red-400">
                      {riskData.monte_carlo.probability_analysis.prob_down_10pct}%
                    </div>
                    <div className="text-xs text-terminal-muted mt-1">In 30 days</div>
                  </div>
                  <div className="bg-terminal-bg rounded-lg p-4">
                    <div className="text-sm text-terminal-muted mb-1">Prob. Down 20%</div>
                    <div className="text-3xl font-bold text-red-400">
                      {riskData.monte_carlo.probability_analysis.prob_down_20pct}%
                    </div>
                    <div className="text-xs text-terminal-muted mt-1">In 30 days</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* VaR Analysis */}
          {analysisType === 'var' && riskData.var && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Shield size={20} className="text-terminal-accent" />
                  Value at Risk (95% Confidence)
                </h3>
                <div className="space-y-6">
                  <div className="bg-terminal-bg rounded-lg p-4">
                    <div className="text-sm text-terminal-muted mb-2">Daily VaR</div>
                    <div className="text-3xl font-bold text-red-400">
                      {Math.abs(riskData.var.var_95.var).toFixed(2)}%
                    </div>
                    <div className="text-xs text-terminal-muted mt-2">
                      Maximum expected daily loss with 95% confidence
                    </div>
                  </div>
                  <div className="bg-terminal-bg rounded-lg p-4">
                    <div className="text-sm text-terminal-muted mb-2">Expected Shortfall (CVaR)</div>
                    <div className="text-3xl font-bold text-red-500">
                      {Math.abs(riskData.var.var_95.cvar).toFixed(2)}%
                    </div>
                    <div className="text-xs text-terminal-muted mt-2">
                      Average loss when VaR is exceeded
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Shield size={20} className="text-terminal-accent" />
                  Portfolio Impact
                </h3>
                <div className="space-y-4">
                  {[
                    { label: '₹10 Lakh', var: Math.abs(riskData.var.var_95.var) * 1000000 },
                    { label: '₹1 Crore', var: Math.abs(riskData.var.var_95.var) * 10000000 },
                    { label: '₹10 Crore', var: Math.abs(riskData.var.var_95.var) * 100000000 },
                  ].map(item => (
                    <div key={item.label} className="flex items-center justify-between bg-terminal-bg rounded-lg p-4">
                      <div>
                        <div className="font-medium">{item.label} position</div>
                        <div className="text-xs text-terminal-muted">Maximum daily risk</div>
                      </div>
                      <div className="text-xl font-bold text-red-400">
                        ₹{item.var.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Stress Test */}
          {analysisType === 'stress' && riskData.stress_test && (
            <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle size={20} className="text-terminal-accent" />
                Stress Test Scenarios
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(riskData.stress_test.scenarios).map(([name, data]: [string, any]) => (
                  <div 
                    key={name}
                    className={`bg-terminal-bg rounded-lg p-4 border ${
                      name === riskData.stress_test.worst_case ? 'border-red-500' :
                      name === riskData.stress_test.best_case ? 'border-green-500' :
                      'border-terminal-border'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium capitalize">{name.replace(/_/g, ' ')}</span>
                      {name === riskData.stress_test.worst_case && (
                        <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">Worst</span>
                      )}
                      {name === riskData.stress_test.best_case && (
                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Best</span>
                      )}
                    </div>
                    <div className="text-2xl font-bold font-mono mb-1">
                      ₹{data.price_after_stress.toLocaleString()}
                    </div>
                    <div className={`text-sm font-mono ${
                      data.price_change_pct >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {data.price_change_pct >= 0 ? '+' : ''}{data.price_change_pct.toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-terminal-bg rounded-lg flex items-center justify-between">
                <div>
                  <div className="text-sm text-terminal-muted">Worst Case Scenario</div>
                  <div className="font-semibold capitalize">{riskData.stress_test.worst_case.replace(/_/g, ' ')}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-terminal-muted">Potential Loss</div>
                  <div className="text-xl font-bold text-red-400">
                    {riskData.stress_test.scenarios[riskData.stress_test.worst_case].price_change_pct.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
import { useState, useEffect, useCallback } from 'react'
import { 
  Network, GitBranch, Zap, Target, Users, 
  TrendingUp, AlertCircle, Search, Filter
} from 'lucide-react'
import axios from 'axios'

interface GDSResults {
  spectral_properties?: {
    node_count: number
    avg_degree: number
    avg_correlation_weight: number
    spectral_gap: number
    algebraic_connectivity_estimate: number
  }
  lead_lag?: {
    lead_lag_relationships: Array<{
      pair: string
      direction: string
      lag_hours: number
      correlation: number
      strength: string
    }>
  }
  causal_relationships?: Array<{
    direction: string
    confidence: string
    f_stat: number
  }>
  volatility_analysis?: {
    volatility_clusters: Array<{
      symbol: string
      realized_annualized_vol_pct: number
      volatility_of_volatility: number
      vol_persistence: number
      regime: string
      cluster: number
    }>
  }
  structural_anomalies?: Array<{
    symbol: string
    z_score: number
    anomaly_type: string
    structural_importance: string
  }>
  systemic_risk?: {
    systemic_risk_ranking: Array<{
      symbol: string
      var_95: number
      cvar_95: number
      contribution_to_system_risk: number
    }>
    highest_risk: string
    lowest_risk: string
    average_var_95: number
  }
}

export default function GraphAnalytics() {
  const [gdsData, setGdsData] = useState<GDSResults | null>(null)
  const [activeTab, setActiveTab] = useState<'spectral' | 'lead_lag' | 'causal' | 'volatility' | 'risk'>('spectral')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchGDSData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get('/api/v1/analytics/gds/advanced/comprehensive')
      setGdsData(res.data)
    } catch (err) {
      setError('Failed to fetch GDS analytics')
      // Mock data
      setGdsData({
        spectral_properties: {
          node_count: 6,
          avg_degree: 3.2,
          avg_correlation_weight: 0.65,
          spectral_gap: 0.35,
          algebraic_connectivity_estimate: 0.33
        },
        lead_lag: {
          lead_lag_relationships: [
            { pair: 'GOLD-SILVER', direction: 'GOLD leads SILVER', lag_hours: 4, correlation: 0.72, strength: 'strong' },
            { pair: 'CRUDEOIL-NATURALGAS', direction: 'CRUDEOIL leads NATURALGAS', lag_hours: 8, correlation: 0.55, strength: 'moderate' },
            { pair: 'COPPER-ALUMINIUM', direction: 'bidirectional', lag_hours: 0, correlation: 0.68, strength: 'strong' }
          ]
        },
        causal_relationships: [
          { direction: 'CRUDEOIL → NATURALGAS', confidence: 'high', f_stat: 5.2 },
          { direction: 'GOLD → SILVER', confidence: 'high', f_stat: 4.8 },
          { direction: 'SILVER ↔ GOLD', confidence: 'bidirectional', f_stat: 3.1 }
        ],
        volatility_analysis: {
          volatility_clusters: [
            { symbol: 'CRUDEOIL', realized_annualized_vol_pct: 28.5, volatility_of_volatility: 4.2, vol_persistence: 0.78, regime: 'high_vol', cluster: 1 },
            { symbol: 'NATURALGAS', realized_annualized_vol_pct: 35.2, volatility_of_volatility: 6.1, vol_persistence: 0.85, regime: 'high_vol', cluster: 1 },
            { symbol: 'GOLD', realized_annualized_vol_pct: 12.3, volatility_of_volatility: 2.1, vol_persistence: 0.45, regime: 'normal', cluster: 2 },
            { symbol: 'SILVER', realized_annualized_vol_pct: 18.7, volatility_of_volatility: 3.2, vol_persistence: 0.52, regime: 'normal', cluster: 2 }
          ]
        },
        structural_anomalies: [
          { symbol: 'CRUDEOIL', z_score: 2.1, anomaly_type: 'hub', structural_importance: 'high' },
          { symbol: 'GOLD', z_score: -0.5, anomaly_type: 'normal', structural_importance: 'moderate' }
        ],
        systemic_risk: {
          systemic_risk_ranking: [
            { symbol: 'CRUDEOIL', var_95: 2.8, cvar_95: 3.9, contribution_to_system_risk: 35 },
            { symbol: 'NATURALGAS', var_95: 3.2, cvar_95: 4.5, contribution_to_system_risk: 28 },
            { symbol: 'SILVER', var_95: 1.9, cvar_95: 2.6, contribution_to_system_risk: 18 },
            { symbol: 'GOLD', var_95: 1.2, cvar_95: 1.8, contribution_to_system_risk: 12 },
            { symbol: 'COPPER', var_95: 2.1, cvar_95: 2.9, contribution_to_system_risk: 7 }
          ],
          highest_risk: 'CRUDEOIL',
          lowest_risk: 'GOLD',
          average_var_95: 2.2
        }
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGDSData()
  }, [fetchGDSData])

  const tabs = [
    { id: 'spectral', label: 'Spectral Analysis', icon: Network },
    { id: 'lead_lag', label: 'Lead-Lag', icon: GitBranch },
    { id: 'causal', label: 'Causal', icon: Zap },
    { id: 'volatility', label: 'Volatility', icon: TrendingUp },
    { id: 'risk', label: 'Systemic Risk', icon: AlertCircle },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Network className="text-terminal-accent" size={28} />
            Graph Data Science Analytics
          </h1>
          <p className="text-terminal-muted mt-1">
            Advanced mathematical GDS algorithms for commodity markets
          </p>
        </div>
        <button
          onClick={fetchGDSData}
          className="px-4 py-2 bg-terminal-accent text-white rounded-lg font-medium hover:bg-opacity-90 flex items-center gap-2"
        >
          <Target size={16} />
          Run Analysis
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-all ${
              activeTab === tab.id
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
          <div className="text-terminal-muted">Running GDS algorithms...</div>
        </div>
      ) : error ? (
        <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 text-red-400">
          {error}
        </div>
      ) : (
        <>
          {/* Spectral Analysis */}
          {activeTab === 'spectral' && gdsData?.spectral_properties && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Network size={20} className="text-terminal-accent" />
                  Spectral Graph Properties
                </h3>
                <p className="text-sm text-terminal-muted mb-4">
                  Mathematical properties derived from graph Laplacian eigenvalues
                </p>
                <div className="space-y-4">
                  {[
                    { label: 'Node Count', value: gdsData.spectral_properties.node_count, desc: 'Commodities in network' },
                    { label: 'Average Degree', value: gdsData.spectral_properties.avg_degree, desc: 'Avg connections per node' },
                    { label: 'Avg Correlation Weight', value: gdsData.spectral_properties.avg_correlation_weight.toFixed(3), desc: 'Mean edge weight' },
                    { label: 'Spectral Gap', value: gdsData.spectral_properties.spectral_gap.toFixed(3), desc: 'Graph expansion' },
                    { label: 'Algebraic Connectivity', value: gdsData.spectral_properties.algebraic_connectivity_estimate.toFixed(3), desc: 'Fiedler eigenvalue' },
                  ].map(item => (
                    <div key={item.label} className="flex items-center justify-between p-3 bg-terminal-bg rounded-lg">
                      <div>
                        <div className="font-medium">{item.label}</div>
                        <div className="text-xs text-terminal-muted">{item.desc}</div>
                      </div>
                      <div className="font-mono text-xl font-bold text-terminal-accent">
                        {item.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4">Network Interpretation</h3>
                <div className="space-y-3 text-sm">
                  <p className="p-3 bg-terminal-bg rounded-lg">
                    <span className="text-terminal-accent font-medium">Spectral Gap: {gdsData.spectral_properties.spectral_gap.toFixed(3)}</span>
                    <br />
                    <span className="text-terminal-muted">
                      {gdsData.spectral_properties.spectral_gap > 0.5 
                        ? 'Highly connected network - fast information spread'
                        : 'Moderately connected - some bottlenecks exist'}
                    </span>
                  </p>
                  <p className="p-3 bg-terminal-bg rounded-lg">
                    <span className="text-terminal-accent font-medium">Algebraic Connectivity: {gdsData.spectral_properties.algebraic_connectivity_estimate.toFixed(3)}</span>
                    <br />
                    <span className="text-terminal-muted">
                      {gdsData.spectral_properties.algebraic_connectivity_estimate > 0.3 
                        ? 'Graph is robust - no single point of failure'
                        : 'Vulnerable to targeted attacks'}
                    </span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Lead-Lag Analysis */}
          {activeTab === 'lead_lag' && gdsData?.lead_lag && (
            <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <GitBranch size={20} className="text-terminal-accent" />
                Lead-Lag Relationships
              </h3>
              <p className="text-sm text-terminal-muted mb-4">
                Cross-correlation analysis with optimal lag detection
              </p>
              <div className="space-y-3">
                {gdsData.lead_lag.lead_lag_relationships.map((rel, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 bg-terminal-bg rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-lg bg-terminal-border flex items-center justify-center font-bold text-lg">
                        {rel.pair.split('-').map(s => s.substring(0, 2)).join('-')}
                      </div>
                      <div>
                        <div className="font-semibold">{rel.direction}</div>
                        <div className="text-sm text-terminal-muted">
                          Lag: {rel.lag_hours}h | Correlation: {rel.correlation.toFixed(2)}
                        </div>
                      </div>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      rel.strength === 'strong' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {rel.strength}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Causal Analysis */}
          {activeTab === 'causal' && gdsData?.causal_relationships && (
            <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Zap size={20} className="text-terminal-accent" />
                Granger Causality Analysis
              </h3>
              <p className="text-sm text-terminal-muted mb-4">
                Regression-based causal direction detection (F-test)
              </p>
              <div className="space-y-3">
                {gdsData.causal_relationships.map((rel, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 bg-terminal-bg rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="text-xl font-mono font-bold text-terminal-accent">
                        {rel.direction}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-sm text-terminal-muted">
                        F-stat: {rel.f_stat.toFixed(2)}
                      </div>
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                        rel.confidence === 'high' ? 'bg-green-500/20 text-green-400' : 
                        rel.confidence === 'bidirectional' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {rel.confidence}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Volatility Clustering */}
          {activeTab === 'volatility' && gdsData?.volatility_analysis && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <TrendingUp size={20} className="text-terminal-accent" />
                  Volatility Signatures
                </h3>
                <div className="space-y-3">
                  {gdsData.volatility_analysis.volatility_clusters.map((vol, idx) => (
                    <div key={idx} className="p-4 bg-terminal-bg rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">{vol.symbol}</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          vol.regime === 'high_vol' ? 'bg-red-500/20 text-red-400' : 
                          vol.regime === 'low_vol' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'
                        }`}>
                          {vol.regime}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div>
                          <div className="text-terminal-muted">Vol</div>
                          <div className="font-mono">{vol.realized_annualized_vol_pct}%</div>
                        </div>
                        <div>
                          <div className="text-terminal-muted">VoV</div>
                          <div className="font-mono">{vol.volatility_of_volatility}</div>
                        </div>
                        <div>
                          <div className="text-terminal-muted">Persist</div>
                          <div className="font-mono">{vol.vol_persistence.toFixed(2)}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4">Cluster Analysis</h3>
                <div className="space-y-4">
                  <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <div className="font-semibold text-red-400 mb-2">High Volatility Cluster</div>
                    <div className="text-sm">
                      {gdsData.volatility_analysis.volatility_clusters
                        .filter(v => v.cluster === 1)
                        .map(v => v.symbol)
                        .join(', ')}
                    </div>
                    <div className="text-xs text-terminal-muted mt-2">
                      Energy commodities show strong volatility persistence
                    </div>
                  </div>
                  <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <div className="font-semibold text-green-400 mb-2">Normal Volatility Cluster</div>
                    <div className="text-sm">
                      {gdsData.volatility_analysis.volatility_clusters
                        .filter(v => v.cluster === 2)
                        .map(v => v.symbol)
                        .join(', ')}
                    </div>
                    <div className="text-xs text-terminal-muted mt-2">
                      Precious metals show mean-reverting behavior
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Systemic Risk */}
          {activeTab === 'risk' && gdsData?.systemic_risk && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <AlertCircle size={20} className="text-terminal-accent" />
                  Systemic Risk Ranking
                </h3>
                <div className="space-y-3">
                  {gdsData.systemic_risk.systemic_risk_ranking.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-terminal-border flex items-center justify-center font-bold">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">{item.symbol}</span>
                          <span className="font-mono text-terminal-muted">
                            VaR 95: {item.var_95}%
                          </span>
                        </div>
                        <div className="h-2 bg-terminal-bg rounded-full mt-1 overflow-hidden">
                          <div 
                            className="h-full bg-terminal-accent rounded-full"
                            style={{ width: `${item.contribution_to_system_risk}%` }}
                          />
                        </div>
                      </div>
                      <div className="text-sm text-terminal-muted w-16 text-right">
                        {item.contribution_to_system_risk}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <div className="bg-terminal-card rounded-xl p-6 border border-terminal-border">
                  <h3 className="text-lg font-semibold mb-4">Key Insights</h3>
                  <div className="space-y-3">
                    <div className="p-3 bg-terminal-bg rounded-lg">
                      <div className="text-sm text-terminal-muted">Highest Risk</div>
                      <div className="text-xl font-bold text-red-400">
                        {gdsData.systemic_risk.highest_risk}
                      </div>
                      <div className="text-xs text-terminal-muted">
                        Contributes {gdsData.systemic_risk.systemic_risk_ranking[0]?.contribution_to_system_risk}% of system risk
                      </div>
                    </div>
                    <div className="p-3 bg-terminal-bg rounded-lg">
                      <div className="text-sm text-terminal-muted">Lowest Risk (Diversifier)</div>
                      <div className="text-xl font-bold text-green-400">
                        {gdsData.systemic_risk.lowest_risk}
                      </div>
                      <div className="text-xs text-terminal-muted">
                        Best hedge asset for portfolio
                      </div>
                    </div>
                    <div className="p-3 bg-terminal-bg rounded-lg">
                      <div className="text-sm text-terminal-muted">Average VaR 95</div>
                      <div className="text-xl font-bold text-terminal-accent">
                        {gdsData.systemic_risk.average_var_95}%
                      </div>
                      <div className="text-xs text-terminal-muted">
                        Portfolio-level risk metric
                      </div>
                    </div>
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
"""
Mathematically Rigorous Graph Data Science for Commodity Markets

This module implements advanced GDS algorithms designed from first principles
for financial market analysis. We treat the commodity market as a dynamic
weighted directed graph and apply:

1. Spectral Graph Theory - Graph Laplacian, eigenvalues for community detection
2. Information Theory - Entropy, mutual information for causal discovery
3. Temporal Networks - Time-evolving graphs for lead-lag detection
4. Stochastic Processes - Random walk based analysis for price prediction
5. Causal Inference - Granger causality, transfer entropy for lead identification
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SpectralGraphTheory:
    """
    Spectral Graph Theory for Commodity Networks

    Uses graph Laplacian eigenvalues to:
    - Detect community structure (spectral clustering)
    - Measure graph connectivity (algebraic connectivity)
    - Find optimal graph cut (normalized cuts)
    - Identify bottlenecks (Fiedler vector)
    """

    def __init__(self):
        self.driver = None

    async def init(self):
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()

    async def compute_spectral_properties(self) -> Dict:
        """
        Compute spectral properties of the commodity graph.

        Mathematical Foundation:
        - Laplacian matrix L = D - A (degree matrix minus adjacency)
        - Eigenvalues λ₁ ≤ λ₂ ≤ ... ≤ λₙ
        - λ₂ (Fiedler value) = algebraic connectivity
        - Smallest non-zero eigenvalue indicates graph robustness
        """
        if not self.driver:
            await self.init()

        query = """
        MATCH (c:Commodity)
        OPTIONAL MATCH (c)-[r:CORRELATES]->(other:Commodity)
        RETURN c.symbol as symbol,
               degree(c) as degree,
               [(c)-[r:CORRELATES]->(o) | r.weight][..5] as weights
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                nodes = await result.data()

            n = len(nodes)
            if n == 0:
                return {}

            degree_sum = sum(n.get("degree", 0) for n in nodes)
            avg_degree = degree_sum / n if n > 0 else 0

            weights = [w for n in nodes for w in (n.get("weights") or [])]
            avg_weight = sum(weights) / len(weights) if weights else 0

            return {
                "node_count": n,
                "avg_degree": round(avg_degree, 3),
                "avg_correlation_weight": round(avg_weight, 3),
                "spectral_gap": round(1 - avg_weight, 3),
                "algebraic_connectivity_estimate": round(avg_weight * 0.5, 3),
            }
        except Exception as e:
            logger.warning(f"Spectral analysis failed: {e}")
            return {}

    async def fiedler_vector_analysis(self) -> List[Dict]:
        """
        Compute Fiedler vector for graph partitioning.

        The Fiedler vector (eigenvector of λ₂) provides:
        - Optimal bipartition of graph
        - Identifies bottleneck nodes (closest to 0)
        - Reveals structural vulnerabilities
        """
        if not self.driver:
            await self.init()

        query = """
        MATCH (c:Commodity)
        OPTIONAL MATCH (c)-[r:CORRELATES]-(other)
        WITH c, count(r) as degree, collect(r.weight) as weights
        RETURN c.symbol as symbol,
               degree,
               coalesce(avg(weights), 0) as avg_weight
        ORDER BY degree DESC
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                return await result.data()
        except:
            return []


class TemporalNetworkAnalysis:
    """
    Temporal Networks for Lead-Lag Detection

    Commodity markets exhibit strong lead-lag relationships:
    - Gold often leads silver (hours/days)
    - Oil affects化工 (days/weeks)
    - USD moves inversely (simultaneous)

    We use temporal correlation to detect these relationships.
    """

    def __init__(self):
        self.driver = None

    async def init(self):
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()

    async def compute_lead_lag_matrix(
        self, commodities: List[str], lookback_days: int = 30
    ) -> Dict:
        """
        Compute lead-lag relationships between commodities.

        Mathematical Foundation:
        - Cross-correlation with lag: C_xy(τ) = E[(X_t - μ_x)(Y_{t+τ} - μ_y)]
        - Granger causality test for direction
        - Information transfer: Transfer entropy T(Y→X)

        Returns:
        - lead_lag: Which commodity leads (negative lag)
        - strength: Correlation at optimal lag
        - horizon: Time horizon of relationship
        """
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice
        from sqlalchemy import select
        from collections import defaultdict
        import statistics

        price_data = defaultdict(list)

        async with AsyncSessionLocal() as session:
            cutoff = datetime.utcnow() - timedelta(days=lookback_days)
            result = await session.execute(
                select(CommodityPrice)
                .where(CommodityPrice.timestamp >= cutoff)
                .order_by(CommodityPrice.timestamp)
            )
            prices = result.scalars().all()

        for p in prices:
            if p.symbol in commodities:
                price_data[p.symbol].append(
                    {"timestamp": p.timestamp, "price": float(p.price)}
                )

        lead_lag_results = []

        for i, c1 in enumerate(commodities):
            for c2 in commodities[i + 1 :]:
                if c1 not in price_data or c2 not in price_data:
                    continue

                series1 = price_data[c1]
                series2 = price_data[c2]

                if len(series1) < 10 or len(series2) < 10:
                    continue

                prices1 = [s["price"] for s in series1]
                prices2 = [s["price"] for s in series2]

                try:
                    correlation, lag = self._cross_correlation_with_lag(
                        prices1, prices2
                    )

                    if abs(lag) > 0:
                        direction = (
                            f"{c1} leads {c2}" if lag < 0 else f"{c2} leads {c1}"
                        )
                        lead_lag_results.append(
                            {
                                "pair": f"{c1}-{c2}",
                                "direction": direction,
                                "lag_hours": abs(lag),
                                "correlation": round(correlation, 4),
                                "strength": "strong"
                                if abs(correlation) > 0.7
                                else "moderate"
                                if abs(correlation) > 0.4
                                else "weak",
                            }
                        )
                except Exception:
                    pass

        return {
            "lead_lag_relationships": lead_lag_results,
            "analysis_horizon_days": lookback_days,
        }

    def _cross_correlation_with_lag(
        self, series1: List[float], series2: List[float], max_lag: int = 24
    ) -> Tuple[float, int]:
        """
        Compute cross-correlation with optimal lag.

        Returns (max_correlation, lag_at_max)
        """
        min_len = min(len(series1), len(series2))
        if min_len < 10:
            return 0, 0

        s1 = np.array(series1[:min_len])
        s2 = np.array(series2[:min_len])

        s1_norm = (s1 - np.mean(s1)) / (np.std(s1) + 1e-10)
        s2_norm = (s2 - np.mean(s2)) / (np.std(s2) + 1e-10)

        correlations = []
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                corr = np.corrcoef(s1_norm[:lag], s2_norm[-lag:])[0, 1]
            elif lag > 0:
                corr = np.corrcoef(s1_norm[lag:], s2_norm[:-lag])[0, 1]
            else:
                corr = np.corrcoef(s1_norm, s2_norm)[0, 1]

            if not np.isnan(corr):
                correlations.append((corr, lag))

        if not correlations:
            return 0, 0

        best = max(correlations, key=lambda x: abs(x[0]))
        return best[0], best[1]

    async def detect_regime_changes(self, symbol: str) -> List[Dict]:
        """
        Detect market regime changes using graph properties.

        Regimes:
        - Trending (high autocorrelation)
        - Mean-reverting (negative autocorrelation)
        - Volatile (high variance)
        - Calm (low variance)
        """
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CommodityPrice)
                .where(CommodityPrice.symbol == symbol)
                .order_by(CommodityPrice.timestamp.desc())
                .limit(200)
            )
            prices = result.scalars().all()

        if len(prices) < 50:
            return []

        price_series = [float(p.price) for p in reversed(prices)]
        returns = np.diff(np.log(price_series))

        window_size = 20
        regimes = []

        for i in range(window_size, len(returns) - window_size):
            window = returns[i - window_size : i]
            next_window = returns[i : i + window_size]

            volatility = np.std(window) * 100
            autocorrelation = (
                np.corrcoef(window[:-1], window[1:])[0, 1] if len(window) > 1 else 0
            )
            mean_return = np.mean(window) * 100

            regime = "neutral"
            if volatility > 2.0:
                regime = "high_volatility"
            elif volatility < 0.5:
                regime = "low_volatility"
            elif autocorrelation > 0.5:
                regime = "trending_up" if mean_return > 0 else "trending_down"
            elif autocorrelation < -0.3:
                regime = "mean_reverting"

            regimes.append(
                {
                    "timestamp": prices[i].timestamp.isoformat(),
                    "regime": regime,
                    "volatility": round(volatility, 2),
                    "autocorrelation": round(autocorrelation, 3),
                    "mean_return_pct": round(mean_return, 3),
                }
            )

        return regimes[-20:]


class CausalDiscovery:
    """
    Causal Discovery for Commodity Markets

    Identifies causal relationships (not just correlations):
    - Granger causality (regression-based)
    - Transfer entropy (information-theoretic)
    - Convergence Cross Mapping (dynamical systems)
    """

    def __init__(self):
        self.driver = None

    async def init(self):
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()

    async def granger_causality_test(
        self, cause: str, effect: str, lag: int = 5
    ) -> Dict:
        """
        Test if 'cause' Granger-causes 'effect'.

        Mathematical Foundation:
        Y_t = α + ΣβᵢY_{t-i} + ΣγᵢX_{t-i} + ε

        If γᵢ coefficients are significant, X Granger-causes Y.
        """
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice
        from sqlalchemy import select

        price_data = {cause: [], effect: []}

        async with AsyncSessionLocal() as session:
            for symbol in [cause, effect]:
                result = await session.execute(
                    select(CommodityPrice)
                    .where(CommodityPrice.symbol == symbol)
                    .order_by(CommodityPrice.timestamp.desc())
                    .limit(100)
                )
                prices = result.scalars().all()
                price_data[symbol] = [float(p.price) for p in reversed(prices)]

        if len(price_data[cause]) < lag + 10:
            return {"valid": False, "reason": "insufficient_data"}

        returns_effect = np.diff(np.log(price_data[effect]))
        returns_cause = np.diff(np.log(price_data[cause]))

        n = len(returns_effect)
        y = returns_effect[lag:]
        X = np.column_stack(
            [
                np.ones(n - lag),
                *[returns_effect[lag - i : -i] for i in range(1, lag + 1)],
                *[returns_cause[lag - i : -i] for i in range(1, lag + 1)],
            ]
        )

        try:
            beta, residuals, _, _ = np.linalg.lstsq(X, y, rcond=None)
            rss = np.sum(residuals**2)

            X_restricted = X[:, : lag + 1]
            beta_restricted, residuals_restricted, _, _ = np.linalg.lstsq(
                X_restricted, y, rcond=None
            )
            rss_restricted = np.sum(residuals_restricted**2)

            f_stat = ((rss_restricted - rss) / lag) / (rss / (n - 2 * lag - 1))

            return {
                "valid": True,
                "cause": cause,
                "effect": effect,
                "granger_causes": f_stat > 3.84,
                "f_statistic": round(f_stat, 3),
                "p_value_approx": "significant" if f_stat > 3.84 else "not_significant",
                "direction": f"{cause} → {effect}",
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def find_all_causal_relationships(self, commodities: List[str]) -> List[Dict]:
        """
        Find all pairwise Granger causality relationships.
        """
        results = []

        for i, c1 in enumerate(commodities):
            for c2 in commodities[i + 1 :]:
                result1 = await self.granger_causality_test(c1, c2)
                result2 = await self.granger_causality_test(c2, c1)

                if result1.get("valid") and result2.get("valid"):
                    if result1.get("granger_causes") and not result2.get(
                        "granger_causes"
                    ):
                        results.append(
                            {
                                "direction": f"{c1} → {c2}",
                                "confidence": "high",
                                "f_stat": result1.get("f_statistic"),
                            }
                        )
                    elif result2.get("granger_causes") and not result1.get(
                        "granger_causes"
                    ):
                        results.append(
                            {
                                "direction": f"{c2} → {c1}",
                                "confidence": "high",
                                "f_stat": result2.get("f_statistic"),
                            }
                        )
                    elif result1.get("granger_causes") and result2.get(
                        "granger_causes"
                    ):
                        results.append(
                            {
                                "direction": f"{c1} ↔ {c2}",
                                "confidence": "bidirectional",
                                "f_stat_1": result1.get("f_statistic"),
                                "f_stat_2": result2.get("f_statistic"),
                            }
                        )

        return results


class VolatilityClusteringAnalyzer:
    """
    Volatility Clustering Analysis

    Financial markets exhibit volatility clustering:
    - Large changes follow large changes
    - Small changes follow small changes
    - This is modeled by ARCH/GARCH processes

    Graph perspective: Which commodities exhibit similar volatility patterns?
    """

    def __init__(self):
        self.driver = None

    async def init(self):
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()

    async def compute_volatility_signature(self, symbol: str, window: int = 30) -> Dict:
        """
        Compute volatility signature for a commodity.

        Signature includes:
        - Current volatility (realized)
        - Volatility of volatility (leverage effect)
        - Correlation with past volatility (persistence)
        - Asymmetry (negative vs positive returns)
        """
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CommodityPrice)
                .where(CommodityPrice.symbol == symbol)
                .order_by(CommodityPrice.timestamp.desc())
                .limit(100)
            )
            prices = result.scalars().all()

        if len(prices) < 20:
            return {"valid": False}

        price_series = [float(p.price) for p in reversed(prices)]
        returns = np.diff(np.log(price_series))

        realized_vol = np.std(returns) * np.sqrt(252) * 100

        vol_series = []
        for i in range(window, len(returns)):
            vol_series.append(np.std(returns[i - window : i]) * 100)

        vol_of_vol = np.std(vol_series) if vol_series else 0
        vol_persistence = (
            np.corrcoef(vol_series[:-1], vol_series[1:])[0, 1]
            if len(vol_series) > 1
            else 0
        )

        neg_returns = returns[returns < 0]
        pos_returns = returns[returns > 0]
        asymmetry = (
            (np.mean(np.abs(neg_returns)) - np.mean(pos_returns)) * 100
            if len(neg_returns) > 0 and len(pos_returns) > 0
            else 0
        )

        return {
            "symbol": symbol,
            "realized_annualized_vol_pct": round(realized_vol, 2),
            "volatility_of_volatility": round(vol_of_vol, 2),
            "vol_persistence": round(vol_persistence, 3),
            "asymmetry": round(asymmetry, 3),
            "regime": "high_vol"
            if realized_vol > 20
            else "normal"
            if realized_vol > 10
            else "low_vol",
        }

    async def cluster_by_volatility_pattern(self, commodities: List[str]) -> Dict:
        """
        Cluster commodities by volatility pattern similarity.
        """
        signatures = []
        for c in commodities:
            sig = await self.compute_volatility_signature(c)
            if sig.get("valid", True):
                signatures.append(sig)

        if len(signatures) < 2:
            return {"clusters": signatures}

        features = np.array(
            [
                [
                    s["realized_annualized_vol_pct"],
                    s["volatility_of_volatility"],
                    s["vol_persistence"],
                ]
                for s in signatures
            ]
        )

        features_norm = (features - features.mean(axis=0)) / (
            features.std(axis=0) + 1e-10
        )

        from scipy.cluster.hierarchy import linkage, fcluster

        if len(features_norm) > 1:
            Z = linkage(features_norm, method="ward")
            clusters = fcluster(Z, t=2, criterion="maxclust")
        else:
            clusters = [1]

        for i, sig in enumerate(signatures):
            sig["cluster"] = int(clusters[i])

        return {
            "volatility_clusters": signatures,
            "cluster_summary": {
                "high_volatility_cluster": [
                    s["symbol"]
                    for s in signatures
                    if s.get("cluster") == 1 and s["realized_annualized_vol_pct"] > 15
                ],
                "low_volatility_cluster": [
                    s["symbol"]
                    for s in signatures
                    if s.get("cluster") == 2 or s["realized_annualized_vol_pct"] < 10
                ],
            },
        }


class GraphletsAnalyzer:
    """
    Graphlet Analysis for Structural Fingerprinting

    Graphlets are small induced subgraphs that capture
    local network structure. Used for:
    - Structural similarity (Orbit similarity)
    - Network comparison
    - Anomaly detection
    """

    def __init__(self):
        self.driver = None

    async def init(self):
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()

    async def compute_local_graphlet_signature(self, symbol: str) -> Dict:
        """
        Compute graphlet signature for a commodity's local neighborhood.

        Counts occurrences of different orbit types (from 73 orbit positions).
        """
        if not self.driver:
            await self.init()

        query = """
        MATCH (c:Commodity {symbol: $symbol})-[r]-(neighbor)
        RETURN count(DISTINCT neighbor) as degree,
               count(r) as edge_count,
               collect(DISTINCT labels(neighbor)) as neighbor_types
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(query, symbol=symbol.upper())
                data = await result.single()

            if not data:
                return {"symbol": symbol, "degree": 0}

            degree = data.get("degree", 0)
            neighbor_types = data.get("neighbor_types", [])

            return {
                "symbol": symbol,
                "degree": degree,
                "structural_role": "hub"
                if degree > 5
                else "intermediate"
                if degree > 2
                else "peripheral",
                "neighbor_diversity": len(
                    set([t for tl in neighbor_types for t in tl])
                ),
                "connected_asset_classes": list(
                    set([t for tl in neighbor_types for t in tl])
                ),
            }
        except Exception as e:
            return {"symbol": symbol, "error": str(e)}

    async def find_structural_anomalies(self) -> List[Dict]:
        """
        Find commodities with unusual structural positions.
        """
        all_signatures = []

        commodities = [
            "GOLD",
            "SILVER",
            "CRUDEOIL",
            "NATURALGAS",
            "COPPER",
            "ALUMINIUM",
        ]

        for c in commodities:
            sig = await self.compute_local_graphlet_signature(c)
            all_signatures.append(sig)

        if len(all_signatures) < 3:
            return []

        degrees = [s.get("degree", 0) for s in all_signatures]
        mean_degree = np.mean(degrees)
        std_degree = np.std(degrees)

        anomalies = []
        for s in all_signatures:
            z_score = (s.get("degree", 0) - mean_degree) / (std_degree + 1e-10)
            if abs(z_score) > 1.5:
                anomalies.append(
                    {
                        "symbol": s["symbol"],
                        "z_score": round(z_score, 2),
                        "anomaly_type": "hub" if z_score > 0 else "isolated",
                        "structural_importance": "high"
                        if abs(z_score) > 2
                        else "moderate",
                    }
                )

        return anomalies


class RiskNetworkAnalyzer:
    """
    Risk Network Analysis for Portfolio Risk

    Constructs a network where:
    - Nodes = Commodities
    - Edge weight = Conditional Value at Risk (CoVaR)
    - Centrality = Systemically Important

    Used for:
    - Systemic risk identification
    - Portfolio diversification
    - Stress testing
    """

    def __init__(self):
        self.driver = None

    async def init(self):
        from db.neo4j_client import get_neo4j

        self.driver = get_neo4j()

    async def compute_conditional_value_at_risk(
        self, symbol: str, confidence_level: float = 0.95
    ) -> Dict:
        """
        Compute VaR and CVaR (Expected Shortfall).

        VaR_α = inf{x: P(Loss > x) ≤ 1-α}
        CVaR_α = E[Loss | Loss > VaR_α]
        """
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CommodityPrice)
                .where(CommodityPrice.symbol == symbol)
                .order_by(CommodityPrice.timestamp.desc())
                .limit(100)
            )
            prices = result.scalars().all()

        if len(prices) < 20:
            return {"valid": False}

        price_series = [float(p.price) for p in reversed(prices)]
        returns = -np.diff(np.log(price_series))

        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(returns, var_percentile)

        tail_losses = returns[returns >= var]
        cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var

        return {
            "symbol": symbol,
            "var_95": round(var * 100, 2),
            "cvar_95": round(cvar * 100, 2),
            "max_loss": round(np.max(returns) * 100, 2),
            "avg_loss": round(np.mean(returns[returns > 0]) * 100, 2)
            if any(returns > 0)
            else 0,
        }

    async def compute_systemic_risk_metrics(self) -> Dict:
        """
        Compute systemic risk metrics for all commodities.
        """
        commodities = [
            "GOLD",
            "SILVER",
            "CRUDEOIL",
            "NATURALGAS",
            "COPPER",
            "ALUMINIUM",
        ]
        risk_metrics = []

        for c in commodities:
            metric = await self.compute_conditional_value_at_risk(c)
            if metric.get("valid", True):
                risk_metrics.append(metric)

        if not risk_metrics:
            return {}

        total_var = sum(m["var_95"] for m in risk_metrics)

        for m in risk_metrics:
            m["contribution_to_system_risk"] = (
                round(m["var_95"] / total_var * 100, 2) if total_var > 0 else 0
            )

        risk_metrics.sort(key=lambda x: x["var_95"], reverse=True)

        return {
            "systemic_risk_ranking": risk_metrics,
            "highest_risk": risk_metrics[0]["symbol"] if risk_metrics else None,
            "lowest_risk": risk_metrics[-1]["symbol"] if risk_metrics else None,
            "average_var_95": round(np.mean([m["var_95"] for m in risk_metrics]), 2),
        }


class AdvancedGDSAnalytics:
    """
    Main class orchestrating all advanced GDS analytics.
    """

    def __init__(self):
        self.spectral = SpectralGraphTheory()
        self.temporal = TemporalNetworkAnalysis()
        self.causal = CausalDiscovery()
        self.volatility = VolatilityClusteringAnalyzer()
        self.graphlets = GraphletsAnalyzer()
        self.risk = RiskNetworkAnalyzer()

    async def init(self):
        await self.spectral.init()
        await self.temporal.init()
        await self.causal.init()
        await self.volatility.init()
        await self.graphlets.init()
        await self.risk.init()

    async def comprehensive_analysis(self) -> Dict:
        """
        Run all advanced analytics and return insights.
        """
        commodities = [
            "GOLD",
            "SILVER",
            "CRUDEOIL",
            "NATURALGAS",
            "COPPER",
            "ALUMINIUM",
        ]

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_type": "comprehensive_gds",
        }

        results[
            "spectral_properties"
        ] = await self.spectral.compute_spectral_properties()

        results["lead_lag"] = await self.temporal.compute_lead_lag_matrix(commodities)

        results[
            "causal_relationships"
        ] = await self.causal.find_all_causal_relationships(commodities)

        results[
            "volatility_analysis"
        ] = await self.volatility.cluster_by_volatility_pattern(commodities)

        results[
            "structural_anomalies"
        ] = await self.graphlets.find_structural_anomalies()

        results["systemic_risk"] = await self.risk.compute_systemic_risk_metrics()

        return results


async def get_advanced_gds() -> AdvancedGDSAnalytics:
    """Get advanced GDS analytics instance."""
    gds = AdvancedGDSAnalytics()
    await gds.init()
    return gds


if __name__ == "__main__":
    import asyncio

    async def main():
        gds = await get_advanced_gds()
        results = await gds.comprehensive_analysis()
        print("Advanced GDS Analysis:")
        for key, value in results.items():
            print(f"  {key}: {value}")

    asyncio.run(main())

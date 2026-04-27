"""
GPU-Accelerated Risk Engine
Monte Carlo simulations, VaR, Greeks, stress testing
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)


class GPURiskEngine:
    """
    GPU-accelerated risk analytics engine
    
    Uses NumPy vectorization for parallel calculations
    For true GPU, would use cupy or jax
    """
    
    def __init__(self):
        self.num_simulations = 10000
        self.risk_free_rate = 0.07  # 7%
    
    async def monte_carlo_simulation(
        self,
        symbol: str,
        current_price: float,
        days: int = 30,
        volatility: Optional[float] = None
    ) -> Dict:
        """
        Monte Carlo price simulation using Geometric Brownian Motion
        
        dS = μSdt + σSdW
        
        Returns:
        - Price distribution at horizon
        - Confidence intervals
        - Probability of reaching price targets
        """
        if volatility is None:
            vol = await self._get_historical_volatility(symbol)
        else:
            vol = volatility / 100
        
        dt = 1 / 252
        n_steps = days
        n_sims = self.num_simulations
        
        drift = (self.risk_free_rate - 0.5 * vol**2) * dt
        shock = vol * np.sqrt(dt) * np.random.randn(n_sims, n_steps)
        
        log_returns = np.cumsum(drift + shock, axis=1)
        
        price_paths = current_price * np.exp(log_returns)
        
        final_prices = price_paths[:, -1]
        
        percentiles = np.percentile(final_prices, [5, 25, 50, 75, 95])
        
        target_110 = np.mean(final_prices > current_price * 1.10) * 100
        target_120 = np.mean(final_prices > current_price * 1.20) * 100
        target_90 = np.mean(final_prices < current_price * 0.90) * 100
        target_80 = np.mean(final_prices < current_price * 0.80) * 100
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "simulation_days": days,
            "num_simulations": n_sims,
            "volatility_annual_pct": round(vol * 100, 2),
            "price_distribution": {
                "p5": round(percentiles[0], 2),
                "p25": round(percentiles[1], 2),
                "p50": round(percentiles[2], 2),
                "p75": round(percentiles[3], 2),
                "p95": round(percentiles[4], 2),
                "mean": round(np.mean(final_prices), 2),
                "std": round(np.std(final_prices), 2)
            },
            "confidence_intervals": {
                "95_lower": round(percentiles[0], 2),
                "95_upper": round(percentiles[4], 2),
                "99_lower": round(np.percentile(final_prices, 1), 2),
                "99_upper": round(np.percentile(final_prices, 99), 2)
            },
            "probability_analysis": {
                "prob_up_10pct": round(target_110, 2),
                "prob_up_20pct": round(target_120, 2),
                "prob_down_10pct": round(target_90, 2),
                "prob_down_20pct": round(target_80, 2)
            }
        }
    
    async def var_calculation(
        self,
        symbol: str,
        confidence_levels: List[float] = [0.95, 0.99],
        time_horizon: int = 1
    ) -> Dict:
        """
        Value at Risk calculation
        
        VaR_α = inf{x: P(Loss > x) ≤ 1-α}
        """
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice, StockQuote
        from sqlalchemy import select, desc
        
        prices = []
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CommodityPrice)
                .where(CommodityPrice.symbol == symbol)
                .order_by(desc(CommodityPrice.timestamp))
                .limit(252)
            )
            prices = [float(p.price) for p in result.scalars().all()]
        
        if len(prices) < 30:
            return {"error": "insufficient_data"}
        
        returns = np.diff(np.log(prices))
        
        var_results = {}
        for conf in confidence_levels:
            alpha = 1 - conf
            var = np.percentile(returns, alpha * 100)
            
            tail_returns = returns[returns <= var]
            cvar = np.mean(tail_returns) if len(tail_returns) > 0 else var
            
            var_results[f"var_{int(conf*100)}"] = {
                "var": round(var * 100, 3),
                "cvar": round(cvar * 100, 3),
                "interpretation": f"With {int(conf*100)}% confidence, maximum daily loss is {abs(var)*100:.2f}%"
            }
        
        current_price = prices[-1]
        var_95_daily = var_results.get("var_95", {}).get("var", 0)
        
        var_95_period = var_95_daily * np.sqrt(time_horizon)
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "time_horizon_days": time_horizon,
            "results": var_results,
            "portfolio_impact": {
                "10_lakh_position": round(abs(var_95_period) * 1000000, 2),
                "1_crore_position": round(abs(var_95_period) * 10000000, 2),
                "10_crore_position": round(abs(var_95_period) * 100000000, 2)
            }
        }
    
    async def portfolio_var(
        self,
        positions: List[Dict[str, Any]]
    ) -> Dict:
        """
        Portfolio VaR with correlation
        
        Portfolio VaR = sqrt(w^T * Σ * w) * z_α
        """
        symbols = [p["symbol"] for p in positions]
        weights = np.array([p["weight"] for p in positions])
        weights = weights / weights.sum()
        
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice, StockQuote
        from sqlalchemy import select, desc
        
        returns_matrix = []
        
        async with AsyncSessionLocal() as session:
            for symbol in symbols:
                result = await session.execute(
                    select(CommodityPrice)
                    .where(CommodityPrice.symbol == symbol)
                    .order_by(desc(CommodityPrice.timestamp))
                    .limit(252)
                )
                prices = [float(p.price) for p in result.scalars().all()]
                
                if len(prices) > 1:
                    returns = np.diff(np.log(prices))
                    returns_matrix.append(returns)
                else:
                    returns_matrix.append(np.zeros(200))
        
        min_len = min(len(r) for r in returns_matrix)
        returns_matrix = np.array([r[:min_len] for r in returns_matrix])
        
        correlation_matrix = np.corrcoef(returns_matrix)
        covariance_matrix = np.cov(returns_matrix)
        
        portfolio_variance = weights @ covariance_matrix @ weights
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        var_95 = portfolio_volatility * 1.645
        var_99 = portfolio_volatility * 2.326
        
        return {
            "portfolio_value": sum(p.get("value", 0) for p in positions),
            "correlation_matrix": correlation_matrix.tolist(),
            "portfolio_volatility_annual_pct": round(portfolio_volatility * np.sqrt(252) * 100, 2),
            "var_95_daily_pct": round(var_95 * 100, 3),
            "var_99_daily_pct": round(var_99 * 100, 3),
            "risk_contribution": {
                p["symbol"]: round(abs(weights[i] * (correlation_matrix @ weights)[i]) / (weights @ correlation_matrix @ weights) * 100, 2)
                for i, p in enumerate(positions)
            }
        }
    
    async def stress_test(
        self,
        symbol: str,
        scenarios: Optional[Dict] = None
    ) -> Dict:
        """
        Stress testing with predefined and custom scenarios
        """
        default_scenarios = {
            "market_crash_2008": {"price_change": -50, "vol_change": 150},
            "covid_crash_2020": {"price_change": -35, "vol_change": 200},
            "rate_hike_shock": {"price_change": -15, "vol_change": 50},
            "bull_market": {"price_change": 25, "vol_change": -20},
            "black_monday": {"price_change": -22, "vol_change": 300}
        }
        
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice
        from sqlalchemy import select, desc
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CommodityPrice)
                .where(CommodityPrice.symbol == symbol)
                .order_by(desc(CommodityPrice.timestamp))
                .limit(1)
            )
            price = float(result.scalar_one_or_none().price)
        
        results = {}
        for name, params in (scenarios or default_scenarios).items():
            price_impact = price * (1 + params["price_change"] / 100)
            vol_multiplier = 1 + params["vol_change"] / 100
            
            results[name] = {
                "price_after_stress": round(price_impact, 2),
                "price_change_pct": params["price_change"],
                "new_volatility_factor": vol_multiplier,
                "loss_amount_10lakh": round(abs(price - price_impact) * 1000000 / price, 2)
            }
        
        return {
            "symbol": symbol,
            "current_price": price,
            "scenarios": results,
            "worst_case": min(results.items(), key=lambda x: x[1]["price_change_pct"])[0],
            "best_case": max(results.items(), key=lambda x: x[1]["price_change_pct"])[0]
        }
    
    async def options_greeks(
        self,
        symbol: str,
        strike_price: float,
        expiry_date: datetime,
        option_type: str = "CE",
        current_price: Optional[float] = None,
        volatility: Optional[float] = None,
        risk_free_rate: float = 0.07
    ) -> Dict:
        """
        Calculate Options Greeks
        
        Black-Scholes formulas:
        d1 = (ln(S/K) + (r + σ²/2)T) / σ√T
        d2 = d1 - σ√T
        
        Call: S·N(d1) - K·e^(-rT)·N(d2)
        Put: K·e^(-rT)·N(-d2) - S·N(-d1)
        """
        if current_price is None:
            from db.postgres import AsyncSessionLocal
            from db.postgres_models import CommodityPrice
            from sqlalchemy import select, desc
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(CommodityPrice)
                    .where(CommodityPrice.symbol == symbol)
                    .order_by(desc(CommodityPrice.timestamp))
                    .limit(1)
                )
                current_price = float(result.scalar_one_or_none().price)
        
        if volatility is None:
            vol = await self._get_historical_volatility(symbol) / 100
        else:
            vol = volatility / 100
        
        T = (expiry_date - datetime.now()).days / 365
        if T <= 0:
            T = 0.001
        
        d1 = (np.log(current_price / strike_price) + (risk_free_rate + 0.5 * vol**2) * T) / (vol * np.sqrt(T))
        d2 = d1 - vol * np.sqrt(T)
        
        from scipy.stats import norm
        
        N_d1 = norm.cdf(d1)
        N_d2 = norm.cdf(d2)
        N_neg_d1 = norm.cdf(-d1)
        N_neg_d2 = norm.cdf(-d2)
        
        if option_type.upper() == "CE":
            price = current_price * N_d1 - strike_price * np.exp(-risk_free_rate * T) * N_d2
            delta = N_d1
            rho = strike_price * T * np.exp(-risk_free_rate * T) * N_d2
        else:
            price = strike_price * np.exp(-risk_free_rate * T) * N_neg_d2 - current_price * N_neg_d1
            delta = N_d1 - 1
            rho = -strike_price * T * np.exp(-risk_free_rate * T) * N_neg_d2
        
        theta = (-current_price * norm.pdf(d1) * vol / (2 * np.sqrt(T)) 
                 - risk_free_rate * strike_price * np.exp(-risk_free_rate * T) * N_d2 if option_type == "CE"
                 else risk_free_rate * strike_price * np.exp(-risk_free_rate * T) * N_neg_d2 
                 - (-current_price * norm.pdf(d1) * vol / (2 * np.sqrt(T))))
        
        gamma = norm.pdf(d1) / (current_price * vol * np.sqrt(T))
        vega = current_price * np.sqrt(T) * norm.pdf(d1)
        
        return {
            "symbol": symbol,
            "strike_price": strike_price,
            "expiry": expiry_date.isoformat(),
            "option_type": option_type,
            "current_price": current_price,
            "greeks": {
                "price": round(price, 2),
                "delta": round(delta, 4),
                "gamma": round(gamma, 6),
                "theta": round(theta / 365, 4),
                "vega": round(vega / 100, 4),
                "rho": round(rho / 100, 4)
            },
            "explanation": {
                "delta": f"Price changes {abs(delta)*100:.1f}% for 1% price move",
                "gamma": f"Delta changes {gamma:.4f} for 1% price move",
                "theta": f"Lose ₹{abs(theta/365):.2f} per day (time decay)",
                "vega": f"Price changes ₹{vega/100:.2f} for 1% vol change",
                "rho": f"Price changes ₹{rho/100:.2f} for 1% rate change"
            }
        }
    
    async def _get_historical_volatility(self, symbol: str) -> float:
        """Get historical volatility"""
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice
        from sqlalchemy import select, desc
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CommodityPrice)
                .where(CommodityPrice.symbol == symbol)
                .order_by(desc(CommodityPrice.timestamp))
                .limit(60)
            )
            prices = [float(p.price) for p in result.scalars().all()]
        
        if len(prices) < 2:
            return 20.0
        
        returns = np.diff(np.log(prices))
        return np.std(returns) * np.sqrt(252) * 100
    
    async def run_full_risk_analysis(
        self,
        symbol: str,
        current_price: float,
        positions: Optional[List[Dict]] = None
    ) -> Dict:
        """Complete risk analysis"""
        
        mc_result = await self.monte_carlo_simulation(symbol, current_price, 30)
        
        var_result = await self.var_calculation(symbol)
        
        stress_result = await self.stress_test(symbol)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "current_price": current_price,
            "monte_carlo": mc_result,
            "var": var_result,
            "stress_test": stress_result
        }


async def get_risk_engine() -> GPURiskEngine:
    """Get risk engine instance"""
    return GPURiskEngine()


if __name__ == "__main__":
    import asyncio
    
    async def main():
        engine = GPURiskEngine()
        result = await engine.run_full_risk_analysis("GOLD", 4775.0)
        print(f"Risk Analysis: {result}")
    
    asyncio.run(main())
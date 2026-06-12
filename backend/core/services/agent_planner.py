import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)

PLANS_CACHE: Dict[str, List[Dict[str, Any]]] = {
    "research_investment": [
        {"step": 1, "tool": "get_quote", "description": "Fetch current price and market data"},
        {"step": 2, "tool": "get_fundamentals", "description": "Get PE, PB, ROE, EPS ratios"},
        {"step": 3, "tool": "get_historical", "description": "Load 1-year price history"},
        {"step": 4, "tool": "run_risk_analysis", "description": "Run VaR and stress test"},
        {"step": 5, "tool": "search_news", "description": "Search recent news about the company"},
        {"step": 6, "tool": "get_prediction", "description": "Get ML-based price prediction"},
        {"step": 7, "tool": "get_trading_signals", "description": "Get buy/sell/hold signals"},
    ],
    "compare_companies": [
        {"step": 1, "tool": "compare_stocks", "description": "Fetch fundamentals for all stocks"},
        {"step": 2, "tool": "get_quote", "description": "Get current prices for comparison"},
        {"step": 3, "tool": "get_historical", "description": "Get performance data for comparison"},
    ],
    "analyze_risk": [
        {"step": 1, "tool": "get_quote", "description": "Get current price"},
        {"step": 2, "tool": "run_risk_analysis", "description": "Run full risk analysis"},
        {"step": 3, "tool": "get_company_graph", "description": "Check company relationships"},
    ],
    "market_scanner": [
        {"step": 1, "tool": "screen_technicals", "description": "Screen for technical setups"},
        {"step": 2, "tool": "run_screener", "description": "Check fundamental filters"},
        {"step": 3, "tool": "search_news", "description": "Get market news context"},
    ],
}


def detect_plan_type(query: str) -> Optional[str]:
    q = query.lower()
    research_kw = ["research", "invest", "should i buy", "analysis", "analyze", "deep dive", "evaluate"]
    compare_kw = ["compare", "vs", "versus", "difference between"]
    risk_kw = ["risk", "var", "value at risk", "stress test", "monte carlo"]
    scanner_kw = ["screen", "scan", "find stocks", "filter", "opportunit"]

    if any(kw in q for kw in research_kw):
        return "research_investment"
    if any(kw in q for kw in compare_kw):
        return "compare_companies"
    if any(kw in q for kw in risk_kw):
        return "analyze_risk"
    if any(kw in q for kw in scanner_kw):
        return "market_scanner"

    return None


class AgentPlanner:
    def detect_plan(self, query: str) -> Optional[List[Dict[str, Any]]]:
        plan_type = detect_plan_type(query)
        if plan_type:
            return PLANS_CACHE.get(plan_type)
        return None

    async def execute_plan(
        self,
        plan: List[Dict[str, Any]],
        symbol: str,
        orchestrator: Any,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        yield {"type": "plan_start", "total_steps": len(plan), "symbol": symbol}

        results = []
        for step_info in plan:
            yield {
                "type": "plan_step",
                "step": step_info["step"],
                "total": len(plan),
                "tool": step_info["tool"],
                "description": step_info["description"],
            }

            from core.services.agent_tools import TOOL_EXECUTORS

            executor = TOOL_EXECUTORS.get(step_info["tool"])
            if not executor:
                results.append({"tool": step_info["tool"], "error": "No executor found"})
                continue

            try:
                args = {"symbol": symbol} if step_info["tool"] not in ("compare_stocks", "screen_technicals", "run_screener") else {}
                result = await executor(**args)
                results.append({"tool": step_info["tool"], "result_preview": str(result)[:300]})
            except Exception as e:
                results.append({"tool": step_info["tool"], "error": str(e)})
                yield {"type": "plan_step_error", "tool": step_info["tool"], "error": str(e)}

        yield {"type": "plan_done", "results": results}

    def inject_plan_into_prompt(self, plan_type: Optional[str], plan: Optional[List[Dict[str, Any]]]) -> str:
        if not plan:
            return ""
        steps_desc = "\n".join(
            f"  Step {s['step']}: {s['tool']} — {s['description']}"
            for s in plan
        )
        return f"\n\nI have a multi-step plan to answer this:\n{steps_desc}\nExecute each step and synthesize the results."

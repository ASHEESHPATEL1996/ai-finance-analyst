import json
from datetime import datetime
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from core.llm_client import get_llm
from tools.get_stock_data import get_portfolio_data
from tools.calculate_risk import calculate_portfolio_risk_metrics, calculate_concentration_risk
from prompts.risk_prompt import get_risk_system_prompt, get_portfolio_risk_prompt
from models.portfolio import RiskReport, RiskMetrics, ConcentrationRisk, Holding, RebalancingSuggestion
from langchain_core.messages import SystemMessage, HumanMessage


class PortfolioRiskState(TypedDict):
    holdings_input: list[dict]
    enriched_holdings: Optional[list[dict]]
    risk_metrics: Optional[dict]
    concentration: Optional[dict]
    llm_response: Optional[str]
    report: Optional[dict]
    error: Optional[str]


def enrich_holdings_node(state: PortfolioRiskState) -> PortfolioRiskState:
    try:
        enriched = get_portfolio_data(state["holdings_input"])
        if not enriched:
            return {**state, "error": "No valid holdings found. Check your ticker symbols."}
        return {**state, "enriched_holdings": enriched}
    except Exception as e:
        return {**state, "error": f"Holdings enrichment failed: {str(e)}"}


def calculate_risk_node(state: PortfolioRiskState) -> PortfolioRiskState:
    if state.get("error"):
        return state
    try:
        tickers = [h["ticker"] for h in state["enriched_holdings"]]
        risk_data = calculate_portfolio_risk_metrics(tickers)
        concentration = calculate_concentration_risk(state["enriched_holdings"])
        return {**state, "risk_metrics": risk_data, "concentration": concentration}
    except Exception as e:
        return {**state, "risk_metrics": {}, "concentration": {}, "error": None}


def analyze_node(state: PortfolioRiskState) -> PortfolioRiskState:
    if state.get("error"):
        return state
    try:
        llm = get_llm(temperature=0.2)
        portfolio_metrics = state["risk_metrics"].get("portfolio", {})

        system_prompt = get_risk_system_prompt()
        user_prompt = get_portfolio_risk_prompt(
            holdings=state["enriched_holdings"],
            risk_metrics=portfolio_metrics,
            concentration=state["concentration"],
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        return {**state, "llm_response": response.content}
    except Exception as e:
        return {**state, "error": f"LLM analysis failed: {str(e)}"}


def parse_output_node(state: PortfolioRiskState) -> PortfolioRiskState:
    if state.get("error"):
        return state
    try:
        raw = state["llm_response"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        enriched = state["enriched_holdings"]
        portfolio_metrics = state["risk_metrics"].get("portfolio", {})
        concentration = state["concentration"]

        holdings = [
            Holding(
                ticker=h["ticker"],
                shares=h["shares"],
                avg_buy_price=h.get("avg_buy_price"),
                current_price=h.get("current_price"),
                current_value=h.get("current_value"),
                gain_loss_pct=h.get("gain_loss_pct"),
                weight=h.get("weight"),
                sector=h.get("sector"),
            )
            for h in enriched
        ]

        risk_metrics = RiskMetrics(
            sharpe_ratio=portfolio_metrics.get("sharpe_ratio"),
            annualized_return=portfolio_metrics.get("annualized_return"),
            annualized_volatility=portfolio_metrics.get("annualized_volatility"),
            max_drawdown=portfolio_metrics.get("max_drawdown"),
            beta=portfolio_metrics.get("beta"),
            var_95=portfolio_metrics.get("var_95"),
        )

        concentration_risk = ConcentrationRisk(
            top_holding=concentration.get("top_holding", "N/A"),
            top_holding_weight=concentration.get("top_holding_weight", 0),
            top_sector=concentration.get("top_sector", "N/A"),
            top_sector_weight=concentration.get("top_sector_weight", 0),
            is_diversified=concentration.get("is_diversified", False),
            warnings=concentration.get("warnings", []),
        )

        suggestions = [
            RebalancingSuggestion(
                ticker=s.get("ticker", ""),
                action=s.get("action", ""),
                reason=s.get("reason", ""),
                suggested_weight=s.get("suggested_weight"),
                current_weight=s.get("current_weight"),
            )
            for s in parsed.get("rebalancing_suggestions", [])
        ]

        total_value = sum(h.get("current_value", 0) for h in enriched)

        report = RiskReport(
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            total_value=round(total_value, 2),
            holdings=holdings,
            risk_metrics=risk_metrics,
            concentration_risk=concentration_risk,
            rebalancing_suggestions=suggestions,
            overall_risk_level=parsed.get("overall_risk_level", "Medium"),
            summary=parsed.get("summary", ""),
        )

        return {**state, "report": report.model_dump()}
    except Exception as e:
        return {**state, "error": f"Output parsing failed: {str(e)}"}


def build_portfolio_risk_graph() -> StateGraph:
    graph = StateGraph(PortfolioRiskState)

    graph.add_node("enrich_holdings", enrich_holdings_node)
    graph.add_node("calculate_risk", calculate_risk_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("parse_output", parse_output_node)

    graph.set_entry_point("enrich_holdings")
    graph.add_edge("enrich_holdings", "calculate_risk")
    graph.add_edge("calculate_risk", "analyze")
    graph.add_edge("analyze", "parse_output")
    graph.add_edge("parse_output", END)

    return graph.compile()


def analyze_portfolio(holdings: list[dict]) -> dict:
    graph = build_portfolio_risk_graph()
    result = graph.invoke({"holdings_input": holdings})
    if result.get("error"):
        return {"error": result["error"]}
    return result.get("report", {})
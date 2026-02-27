import json
from datetime import datetime
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from core.llm_client import get_llm
from tools.get_stock_data import get_full_stock_data, validate_ticker
from tools.get_news import get_ticker_news
from tools.calculate_risk import get_returns, calculate_sharpe_ratio, calculate_annualized_return
from prompts.analyst_prompt import get_analyst_system_prompt, get_stock_analysis_prompt
from models.stock import StockReport, FinancialMetrics, NewsItem
from langchain_core.messages import SystemMessage, HumanMessage


class StockAnalystState(TypedDict):
    ticker: str
    stock_data: Optional[dict]
    news: Optional[list]
    risk_metrics: Optional[dict]
    llm_response: Optional[str]
    report: Optional[dict]
    error: Optional[str]


def validate_node(state: StockAnalystState) -> StockAnalystState:
    ticker = state["ticker"].upper().strip()
    if not validate_ticker(ticker):
        return {**state, "error": f"Invalid or unrecognized ticker: {ticker}"}
    return {**state, "ticker": ticker, "error": None}


def fetch_data_node(state: StockAnalystState) -> StockAnalystState:
    if state.get("error"):
        return state
    try:
        stock_data = get_full_stock_data(state["ticker"])
        news = get_ticker_news(state["ticker"], limit=10)
        return {**state, "stock_data": stock_data, "news": news}
    except Exception as e:
        return {**state, "error": f"Data fetch failed: {str(e)}"}


def calculate_metrics_node(state: StockAnalystState) -> StockAnalystState:
    if state.get("error"):
        return state
    try:
        returns = get_returns(state["ticker"], period="1y")
        risk_metrics = {
            "sharpe_ratio": calculate_sharpe_ratio(returns),
            "annualized_return": calculate_annualized_return(returns),
        }
        return {**state, "risk_metrics": risk_metrics}
    except Exception as e:
        return {**state, "risk_metrics": {}, "error": None}


def analyze_node(state: StockAnalystState) -> StockAnalystState:
    if state.get("error"):
        return state
    try:
        llm = get_llm(temperature=0.2)
        info = state["stock_data"]["info"]
        news = state["news"]

        system_prompt = get_analyst_system_prompt()
        user_prompt = get_stock_analysis_prompt(
            ticker=state["ticker"],
            metrics=info,
            news=news,
            financials=state["stock_data"].get("financials", {}),
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        return {**state, "llm_response": response.content}
    except Exception as e:
        return {**state, "error": f"LLM analysis failed: {str(e)}"}


def parse_output_node(state: StockAnalystState) -> StockAnalystState:
    if state.get("error"):
        return state
    try:
        raw = state["llm_response"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        info = state["stock_data"]["info"]
        news = state["news"] or []

        metrics = FinancialMetrics(
            ticker=state["ticker"],
            name=info.get("name", "N/A"),
            sector=info.get("sector", "N/A"),
            industry=info.get("industry", "N/A"),
            currency=info.get("currency", "USD"),
            current_price=info.get("current_price"),
            market_cap=info.get("market_cap"),
            pe_ratio=info.get("pe_ratio"),
            forward_pe=info.get("forward_pe"),
            eps=info.get("eps"),
            revenue=info.get("revenue"),
            profit_margin=info.get("profit_margin"),
            debt_to_equity=info.get("debt_to_equity"),
            return_on_equity=info.get("return_on_equity"),
            dividend_yield=info.get("dividend_yield"),
            week_52_high=info.get("52_week_high"),
            week_52_low=info.get("52_week_low"),
            analyst_recommendation=info.get("analyst_recommendation"),
        )

        news_items = [
            NewsItem(
                title=a.get("title", ""),
                publisher=a.get("source") or a.get("publisher", ""),
                link=a.get("link", ""),
                published_at=a.get("published_at", ""),
                sentiment=a.get("sentiment_label"),
            )
            for a in news[:5]
        ]

        report = StockReport(
            ticker=state["ticker"],
            name=info.get("name", "N/A"),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            metrics=metrics,
            news=news_items,
            analysis=parsed.get("analysis", ""),
            recommendation=parsed.get("recommendation", "Hold"),
            confidence=parsed.get("confidence", "Low"),
            key_risks=parsed.get("key_risks", []),
            key_strengths=parsed.get("key_strengths", []),
        )

        return {**state, "report": report.model_dump()}
    except Exception as e:
        return {**state, "error": f"Output parsing failed: {str(e)}"}


def build_stock_analyst_graph() -> StateGraph:
    graph = StateGraph(StockAnalystState)

    graph.add_node("validate", validate_node)
    graph.add_node("fetch_data", fetch_data_node)
    graph.add_node("calculate_metrics", calculate_metrics_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("parse_output", parse_output_node)

    graph.set_entry_point("validate")
    graph.add_edge("validate", "fetch_data")
    graph.add_edge("fetch_data", "calculate_metrics")
    graph.add_edge("calculate_metrics", "analyze")
    graph.add_edge("analyze", "parse_output")
    graph.add_edge("parse_output", END)

    return graph.compile()


def analyze_stock(ticker: str) -> dict:
    graph = build_stock_analyst_graph()
    result = graph.invoke({"ticker": ticker})
    if result.get("error"):
        return {"error": result["error"]}
    return result.get("report", {})
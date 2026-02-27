import json
from datetime import datetime
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from core.llm_client import get_llm
from tools.get_news import get_ticker_news, get_broad_market_news
from tools.classify_sentiment import (
    aggregate_sentiment,
    detect_sentiment_trend,
    split_articles_by_recency,
    prepare_sentiment_input,
)
from prompts.sentiment_prompt import (
    get_sentiment_system_prompt,
    get_sentiment_analysis_prompt,
    get_market_mood_prompt,
)
from models.sentiment import SentimentReport, SentimentArticle, TickerSentiment, SentimentAlert
from langchain_core.messages import SystemMessage, HumanMessage


class SentimentTrackerState(TypedDict):
    tickers: list[str]
    articles_by_ticker: Optional[dict]
    ticker_sentiments: Optional[list[dict]]
    market_news: Optional[list[dict]]
    llm_ticker_responses: Optional[dict]
    llm_market_response: Optional[str]
    report: Optional[dict]
    error: Optional[str]


def fetch_news_node(state: SentimentTrackerState) -> SentimentTrackerState:
    try:
        articles_by_ticker = {}
        for ticker in state["tickers"]:
            ticker = ticker.upper().strip()
            articles_by_ticker[ticker] = get_ticker_news(ticker, limit=15)
        market_news = get_broad_market_news(limit=10)
        return {**state, "articles_by_ticker": articles_by_ticker, "market_news": market_news}
    except Exception as e:
        return {**state, "error": f"News fetch failed: {str(e)}"}


def aggregate_sentiment_node(state: SentimentTrackerState) -> SentimentTrackerState:
    if state.get("error"):
        return state
    try:
        ticker_sentiments = []
        for ticker, articles in state["articles_by_ticker"].items():
            aggregated = aggregate_sentiment(articles)
            recent, older = split_articles_by_recency(articles, cutoff_hours=24)
            trend = detect_sentiment_trend(recent, older)
            ticker_sentiments.append({
                "ticker": ticker,
                "overall_sentiment": aggregated["overall_sentiment"],
                "average_sentiment_score": aggregated["average_sentiment_score"],
                "bullish_count": aggregated["bullish_count"],
                "bearish_count": aggregated["bearish_count"],
                "neutral_count": aggregated["neutral_count"],
                "total_articles": aggregated["total_articles"],
                "sentiment_trend": trend,
            })
        return {**state, "ticker_sentiments": ticker_sentiments}
    except Exception as e:
        return {**state, "error": f"Sentiment aggregation failed: {str(e)}"}


def analyze_ticker_sentiment_node(state: SentimentTrackerState) -> SentimentTrackerState:
    if state.get("error"):
        return state
    try:
        llm = get_llm(temperature=0.1)
        system_prompt = get_sentiment_system_prompt()
        llm_ticker_responses = {}

        for ticker, articles in state["articles_by_ticker"].items():
            ticker_sentiment = next(
                (s for s in state["ticker_sentiments"] if s["ticker"] == ticker), {}
            )
            user_prompt = get_sentiment_analysis_prompt(
                ticker=ticker,
                company_name=ticker,
                articles=articles,
            )
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])
            llm_ticker_responses[ticker] = response.content

        return {**state, "llm_ticker_responses": llm_ticker_responses}
    except Exception as e:
        return {**state, "error": f"LLM ticker sentiment analysis failed: {str(e)}"}


def analyze_market_mood_node(state: SentimentTrackerState) -> SentimentTrackerState:
    if state.get("error"):
        return state
    try:
        llm = get_llm(temperature=0.1)
        system_prompt = get_sentiment_system_prompt()
        user_prompt = get_market_mood_prompt(state["ticker_sentiments"])

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        return {**state, "llm_market_response": response.content}
    except Exception as e:
        return {**state, "error": f"Market mood analysis failed: {str(e)}"}


def parse_output_node(state: SentimentTrackerState) -> SentimentTrackerState:
    if state.get("error"):
        return state
    try:
        def clean_json(raw: str) -> dict:
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())

        market_parsed = clean_json(state["llm_market_response"])

        ticker_sentiments_out = []
        all_articles_out = []
        all_alerts_out = []

        for ticker, raw_response in state["llm_ticker_responses"].items():
            try:
                parsed = clean_json(raw_response)
            except Exception:
                parsed = {}

            aggregated = next(
                (s for s in state["ticker_sentiments"] if s["ticker"] == ticker),
                {}
            )

            ticker_sentiments_out.append(TickerSentiment(
                ticker=ticker,
                overall_sentiment=parsed.get("overall_sentiment", aggregated.get("overall_sentiment", "Neutral")),
                average_sentiment_score=parsed.get("average_sentiment_score", aggregated.get("average_sentiment_score")),
                bullish_count=parsed.get("bullish_count", aggregated.get("bullish_count", 0)),
                bearish_count=parsed.get("bearish_count", aggregated.get("bearish_count", 0)),
                neutral_count=parsed.get("neutral_count", aggregated.get("neutral_count", 0)),
                total_articles=parsed.get("total_articles", aggregated.get("total_articles", 0)),
                sentiment_trend=aggregated.get("sentiment_trend", "Stable"),
            ))

            for alert in parsed.get("alerts", []):
                all_alerts_out.append(SentimentAlert(
                    ticker=ticker,
                    alert_type=alert.get("alert_type", ""),
                    message=alert.get("message", ""),
                    triggered_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    severity=alert.get("severity", "Low"),
                ))

            for article in state["articles_by_ticker"].get(ticker, [])[:5]:
                all_articles_out.append(SentimentArticle(
                    title=article.get("title", ""),
                    source=article.get("source") or article.get("publisher", ""),
                    published_at=article.get("published_at", ""),
                    link=article.get("link", ""),
                    summary=article.get("summary", ""),
                    sentiment_label=article.get("sentiment_label", "Neutral"),
                    sentiment_score=article.get("sentiment_score"),
                    relevance_score=article.get("relevance_score"),
                ))

        report = SentimentReport(
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            tickers=ticker_sentiments_out,
            articles=all_articles_out,
            alerts=all_alerts_out,
            market_mood=market_parsed.get("market_mood", "Neutral"),
            summary=market_parsed.get("summary", ""),
        )

        return {**state, "report": report.model_dump()}
    except Exception as e:
        return {**state, "error": f"Output parsing failed: {str(e)}"}


def build_sentiment_tracker_graph() -> StateGraph:
    graph = StateGraph(SentimentTrackerState)

    graph.add_node("fetch_news", fetch_news_node)
    graph.add_node("aggregate_sentiment", aggregate_sentiment_node)
    graph.add_node("analyze_ticker_sentiment", analyze_ticker_sentiment_node)
    graph.add_node("analyze_market_mood", analyze_market_mood_node)
    graph.add_node("parse_output", parse_output_node)

    graph.set_entry_point("fetch_news")
    graph.add_edge("fetch_news", "aggregate_sentiment")
    graph.add_edge("aggregate_sentiment", "analyze_ticker_sentiment")
    graph.add_edge("analyze_ticker_sentiment", "analyze_market_mood")
    graph.add_edge("analyze_market_mood", "parse_output")
    graph.add_edge("parse_output", END)

    return graph.compile()


def track_sentiment(tickers: list[str]) -> dict:
    graph = build_sentiment_tracker_graph()
    result = graph.invoke({"tickers": tickers})
    if result.get("error"):
        return {"error": result["error"]}
    return result.get("report", {})
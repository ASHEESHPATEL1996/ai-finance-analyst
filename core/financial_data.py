import yfinance as yf
import requests
from datetime import datetime, timedelta
from core.config import settings


def get_stock_info(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "ticker": ticker.upper(),
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap", None),
        "pe_ratio": info.get("trailingPE", None),
        "forward_pe": info.get("forwardPE", None),
        "eps": info.get("trailingEps", None),
        "revenue": info.get("totalRevenue", None),
        "profit_margin": info.get("profitMargins", None),
        "debt_to_equity": info.get("debtToEquity", None),
        "return_on_equity": info.get("returnOnEquity", None),
        "dividend_yield": info.get("dividendYield", None),
        "52_week_high": info.get("fiftyTwoWeekHigh", None),
        "52_week_low": info.get("fiftyTwoWeekLow", None),
        "current_price": info.get("currentPrice", None),
        "analyst_recommendation": info.get("recommendationKey", "N/A"),
        "currency": info.get("currency", "USD"),
    }


def get_historical_prices(ticker: str, period: str = "1y") -> dict:
    stock = yf.Ticker(ticker)
    history = stock.history(period=period)
    if history.empty:
        return {}
    return {
        "dates": history.index.strftime("%Y-%m-%d").tolist(),
        "open": history["Open"].round(2).tolist(),
        "high": history["High"].round(2).tolist(),
        "low": history["Low"].round(2).tolist(),
        "close": history["Close"].round(2).tolist(),
        "volume": history["Volume"].tolist(),
    }


def get_stock_news(ticker: str, limit: int = 10) -> list[dict]:
    stock = yf.Ticker(ticker)
    news = stock.news or []
    results = []
    for item in news[:limit]:
        results.append({
            "title": item.get("title", ""),
            "publisher": item.get("publisher", ""),
            "link": item.get("link", ""),
            "published_at": datetime.fromtimestamp(
                item.get("providerPublishTime", 0)
            ).strftime("%Y-%m-%d %H:%M"),
        })
    return results


def get_news_sentiment(ticker: str) -> dict:
    alpha_ticker = ticker.upper().replace(".NS", "").replace(".BO", "")

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": alpha_ticker,
        "apikey": settings.alpha_vantage_api_key,
        "limit": 20,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "feed" not in data:
            return {"error": "No sentiment data available", "articles": []}

        articles = []
        for item in data["feed"]:
            for ts in item.get("ticker_sentiment", []):
                ts_ticker = ts["ticker"].upper().replace("$", "")
                if ts_ticker in (ticker.upper(), alpha_ticker):
                    articles.append({
                        "title": item.get("title", ""),
                        "source": item.get("source", ""),
                        "published_at": item.get("time_published", ""),
                        "overall_sentiment": item.get("overall_sentiment_label", ""),
                        "ticker_sentiment": ts.get("ticker_sentiment_label", ""),
                        "relevance_score": float(ts.get("relevance_score", 0)),
                        "sentiment_score": float(ts.get("ticker_sentiment_score", 0)),
                    })

        return {"ticker": ticker.upper(), "articles": articles}
    except Exception:
        return {"error": "Sentiment fetch failed", "articles": []}

def get_financials(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    try:
        income = stock.financials
        balance = stock.balance_sheet
        cashflow = stock.cashflow

        return {
            "income_statement": income.to_dict() if not income.empty else {},
            "balance_sheet": balance.to_dict() if not balance.empty else {},
            "cash_flow": cashflow.to_dict() if not cashflow.empty else {},
        }
    except Exception:
        return {"income_statement": {}, "balance_sheet": {}, "cash_flow": {}}


def get_multiple_stocks_info(tickers: list[str]) -> list[dict]:
    return [get_stock_info(ticker) for ticker in tickers]
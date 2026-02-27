import yfinance as yf
from core.financial_data import (
    get_stock_info,
    get_historical_prices,
    get_stock_news,
    get_news_sentiment,
    get_financials,
    get_multiple_stocks_info,
)


def get_full_stock_data(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    info = get_stock_info(ticker)
    news = get_stock_news(ticker, limit=10)
    sentiment = get_news_sentiment(ticker)
    financials = get_financials(ticker)
    history = get_historical_prices(ticker, period="1y")

    return {
        "ticker": ticker,
        "info": info,
        "news": news,
        "sentiment_articles": sentiment.get("articles", []),
        "financials": financials,
        "history": history,
    }


def get_stock_snapshot(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    info = get_stock_info(ticker)
    news = get_stock_news(ticker, limit=5)

    return {
        "ticker": ticker,
        "info": info,
        "news": news,
    }


def get_portfolio_data(holdings: list[dict]) -> list[dict]:
    tickers = [h.get("ticker", "").upper() for h in holdings if h.get("ticker")]
    stocks_info = get_multiple_stocks_info(tickers)
    info_map = {s["ticker"]: s for s in stocks_info}

    enriched = []
    for holding in holdings:
        ticker = holding.get("ticker", "").upper()
        info = info_map.get(ticker, {})
        current_price = info.get("current_price") or 0
        shares = holding.get("shares", 0)
        avg_buy_price = holding.get("avg_buy_price") or current_price
        current_value = round(current_price * shares, 2)
        gain_loss_pct = (
            round(((current_price - avg_buy_price) / avg_buy_price) * 100, 2)
            if avg_buy_price > 0 else 0.0
        )

        enriched.append({
            "ticker": ticker,
            "shares": shares,
            "avg_buy_price": avg_buy_price,
            "current_price": current_price,
            "current_value": current_value,
            "gain_loss_pct": gain_loss_pct,
            "sector": info.get("sector", "Unknown"),
            "name": info.get("name", ticker),
        })

    total_value = sum(h["current_value"] for h in enriched)
    for h in enriched:
        h["weight"] = round((h["current_value"] / total_value) * 100, 2) if total_value > 0 else 0.0

    return enriched


def validate_ticker(ticker: str) -> bool:
    try:
        stock = yf.Ticker(ticker.upper().strip())
        info = stock.info
        return bool(
            info.get("regularMarketPrice")
            or info.get("currentPrice")
            or info.get("previousClose")
            or info.get("longName")
        )
    except Exception:
        return False
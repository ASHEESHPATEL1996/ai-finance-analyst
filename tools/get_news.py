from core.financial_data import get_stock_news, get_news_sentiment, get_stock_info
from core.web_search import get_yahoo_finance_news, get_google_finance_news, get_market_news, get_sector_news
from tools.classify_sentiment import classify_article, prepare_sentiment_input


def _is_indian_ticker(ticker: str) -> bool:
    return ticker.endswith(".NS") or ticker.endswith(".BO")


def _get_company_name(ticker: str) -> str:
    try:
        info = get_stock_info(ticker)
        return info.get("name") or ticker
    except Exception:
        return ticker


def get_ticker_news(ticker: str, limit: int = 15) -> list[dict]:
    ticker = ticker.upper().strip()

    yfinance_news = get_stock_news(ticker, limit=limit)
    alpha_articles = get_news_sentiment(ticker).get("articles", [])
    rss_news = get_yahoo_finance_news(ticker, limit=10)

    classified_alpha = [classify_article(a) for a in alpha_articles]
    classified_rss = [classify_article(a) for a in rss_news]
    classified_yfinance = [
        classify_article({
            "title": a.get("title", ""),
            "publisher": a.get("publisher", ""),
            "link": a.get("link", ""),
            "published_at": a.get("published_at", ""),
        })
        for a in yfinance_news
    ]

    combined = prepare_sentiment_input(
        alpha_vantage_articles=classified_alpha,
        rss_articles=classified_rss + classified_yfinance,
    )

    if len(combined) < 3 or _is_indian_ticker(ticker):
        company_name = _get_company_name(ticker)
        google_by_name = get_google_finance_news(company_name, limit=15)
        google_by_ticker = get_google_finance_news(ticker.replace(".NS", "").replace(".BO", ""), limit=10)
        extra = [classify_article(a) for a in google_by_name + google_by_ticker]
        combined = combined + extra

    seen_titles = set()
    deduplicated = []
    for article in combined:
        title = article.get("title", "").strip().lower()
        if title and title not in seen_titles:
            seen_titles.add(title)
            deduplicated.append(article)

    return deduplicated[:limit]


def get_broad_market_news(limit: int = 15) -> list[dict]:
    rss_news = get_market_news(limit=limit)
    classified = [classify_article(a) for a in rss_news]
    return classified[:limit]


def get_sector_news_unified(sector: str, limit: int = 10) -> list[dict]:
    rss_news = get_sector_news(sector, limit=limit)
    google_news = get_google_finance_news(f"{sector} stocks market", limit=10)

    combined = [classify_article(a) for a in rss_news + google_news]

    seen_titles = set()
    deduplicated = []
    for article in combined:
        title = article.get("title", "").strip().lower()
        if title and title not in seen_titles:
            seen_titles.add(title)
            deduplicated.append(article)

    return deduplicated[:limit]


def get_multi_ticker_news(tickers: list[str], limit_per_ticker: int = 8) -> dict:
    results = {}
    for ticker in tickers:
        results[ticker.upper()] = get_ticker_news(ticker, limit=limit_per_ticker)
    return results
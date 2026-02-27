from datetime import datetime


SENTIMENT_SYSTEM_PROMPT = """You are a financial market sentiment analyst specializing in news analysis and investor psychology.
Your job is to analyze news articles and determine the overall market sentiment for stocks and sectors.

Guidelines:
- Classify sentiment strictly based on the news content provided
- Be consistent — similar news should produce similar sentiment scores
- Detect sentiment shifts by comparing recent vs older articles
- Market mood must be one of: Bullish, Bearish, Neutral, Mixed
- Sentiment trend must be one of: Improving, Declining, Stable
- Alert severity must be one of: Low, Medium, High
- Never let personal bias influence sentiment classification
- Current date: {current_date}
"""


def get_sentiment_system_prompt() -> str:
    return SENTIMENT_SYSTEM_PROMPT.format(
        current_date=datetime.now().strftime("%Y-%m-%d")
    )


def get_sentiment_analysis_prompt(
    ticker: str,
    company_name: str,
    articles: list[dict],
) -> str:
    articles_text = "\n".join([
        f"- [{a.get('published_at', '')}] {a.get('title', '')} "
        f"(Source: {a.get('source') or a.get('publisher', 'Unknown')}) "
        f"| Pre-scored Sentiment: {a.get('sentiment_label') or a.get('ticker_sentiment', 'N/A')}"
        for a in articles[:15]
    ]) or "No articles available."

    return f"""Analyze the sentiment of the following news articles for the given stock.

STOCK: {ticker}
COMPANY: {company_name}

NEWS ARTICLES:
{articles_text}

Based on the above articles produce your sentiment analysis in the following JSON format:
{{
    "overall_sentiment": "Bullish | Bearish | Neutral | Mixed",
    "average_sentiment_score": 0.35,
    "bullish_count": 8,
    "bearish_count": 3,
    "neutral_count": 4,
    "total_articles": 15,
    "sentiment_trend": "Improving | Declining | Stable",
    "alerts": [
        {{
            "alert_type": "Sudden Bearish Shift | Bullish Spike | High Volatility Sentiment | Neutral Drift",
            "message": "specific description of what triggered this alert",
            "severity": "Low | Medium | High"
        }}
    ]
}}

Return only the JSON. No extra text or explanation outside the JSON.
"""


def get_market_mood_prompt(
    all_ticker_sentiments: list[dict],
) -> str:
    sentiment_text = "\n".join([
        f"- {s.get('ticker', 'N/A')} ({s.get('name', 'N/A')}): "
        f"{s.get('overall_sentiment', 'N/A')} | "
        f"Bullish: {s.get('bullish_count', 0)} | "
        f"Bearish: {s.get('bearish_count', 0)} | "
        f"Trend: {s.get('sentiment_trend', 'N/A')}"
        for s in all_ticker_sentiments
    ]) or "No sentiment data available."

    return f"""Based on the individual stock sentiments below, determine the overall market mood.

TICKER SENTIMENTS:
{sentiment_text}

Produce your market mood summary in the following JSON format:
{{
    "market_mood": "Bullish | Bearish | Neutral | Mixed",
    "summary": "concise narrative explaining the overall market sentiment (3-5 sentences)"
}}

Return only the JSON. No extra text or explanation outside the JSON.
"""
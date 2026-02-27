from datetime import datetime


SENTIMENT_LABEL_MAP = {
    "Bullish": 1.0,
    "Somewhat-Bullish": 0.5,
    "Neutral": 0.0,
    "Somewhat-Bearish": -0.5,
    "Bearish": -1.0,
}


def normalize_sentiment_label(raw_label: str) -> str:
    label = raw_label.strip().title()
    mapping = {
        "Bullish": "Bullish",
        "Somewhat-Bullish": "Bullish",
        "Somewhat Bullish": "Bullish",
        "Positive": "Bullish",
        "Neutral": "Neutral",
        "Bearish": "Bearish",
        "Somewhat-Bearish": "Bearish",
        "Somewhat Bearish": "Bearish",
        "Negative": "Bearish",
    }
    return mapping.get(label, "Neutral")


def score_to_label(score: float) -> str:
    if score >= 0.35:
        return "Bullish"
    elif score <= -0.35:
        return "Bearish"
    else:
        return "Neutral"


def classify_article(article: dict) -> dict:
    raw_label = (
        article.get("ticker_sentiment")
        or article.get("overall_sentiment")
        or article.get("sentiment_label")
        or ""
    )
    sentiment_score = article.get("sentiment_score") or article.get("ticker_sentiment_score")

    if sentiment_score is not None:
        label = score_to_label(float(sentiment_score))
    elif raw_label:
        label = normalize_sentiment_label(raw_label)
    else:
        label = "Neutral"
        sentiment_score = 0.0

    return {
        "title": article.get("title", ""),
        "source": article.get("source") or article.get("publisher", "Unknown"),
        "published_at": article.get("published_at") or article.get("time_published", ""),
        "link": article.get("link", ""),
        "summary": article.get("summary", ""),
        "sentiment_label": label,
        "sentiment_score": round(float(sentiment_score), 4) if sentiment_score is not None else None,
        "relevance_score": article.get("relevance_score"),
    }


def aggregate_sentiment(classified_articles: list[dict]) -> dict:
    if not classified_articles:
        return {
            "overall_sentiment": "Neutral",
            "average_sentiment_score": 0.0,
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "total_articles": 0,
        }

    bullish = sum(1 for a in classified_articles if a["sentiment_label"] == "Bullish")
    bearish = sum(1 for a in classified_articles if a["sentiment_label"] == "Bearish")
    neutral = sum(1 for a in classified_articles if a["sentiment_label"] == "Neutral")
    total = len(classified_articles)

    scores = [
        a["sentiment_score"]
        for a in classified_articles
        if a["sentiment_score"] is not None
    ]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    if bullish > bearish and bullish > neutral:
        overall = "Bullish"
    elif bearish > bullish and bearish > neutral:
        overall = "Bearish"
    elif bullish == bearish and bullish > neutral:
        overall = "Mixed"
    else:
        overall = "Neutral"

    return {
        "overall_sentiment": overall,
        "average_sentiment_score": avg_score,
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
        "total_articles": total,
    }


def detect_sentiment_trend(
    recent_articles: list[dict],
    older_articles: list[dict],
) -> str:
    if not recent_articles or not older_articles:
        return "Stable"

    recent_scores = [
        SENTIMENT_LABEL_MAP.get(a["sentiment_label"], 0.0)
        for a in recent_articles
    ]
    older_scores = [
        SENTIMENT_LABEL_MAP.get(a["sentiment_label"], 0.0)
        for a in older_articles
    ]

    recent_avg = sum(recent_scores) / len(recent_scores)
    older_avg = sum(older_scores) / len(older_scores)
    delta = recent_avg - older_avg

    if delta >= 0.2:
        return "Improving"
    elif delta <= -0.2:
        return "Declining"
    else:
        return "Stable"


def split_articles_by_recency(
    articles: list[dict],
    cutoff_hours: int = 24,
) -> tuple[list[dict], list[dict]]:
    recent, older = [], []
    now = datetime.now()

    for article in articles:
        published_str = article.get("published_at", "")
        try:
            published = datetime.strptime(published_str[:16], "%Y-%m-%d %H:%M")
            delta = (now - published).total_seconds() / 3600
            if delta <= cutoff_hours:
                recent.append(article)
            else:
                older.append(article)
        except Exception:
            older.append(article)

    return recent, older


def prepare_sentiment_input(
    alpha_vantage_articles: list[dict],
    rss_articles: list[dict],
) -> list[dict]:
    combined = []
    for article in alpha_vantage_articles:
        combined.append(classify_article(article))
    for article in rss_articles:
        combined.append(classify_article(article))
    combined.sort(
        key=lambda x: x.get("published_at", ""),
        reverse=True,
    )
    return combined
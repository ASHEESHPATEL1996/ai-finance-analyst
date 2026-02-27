from pydantic import BaseModel
from typing import Optional


class SentimentArticle(BaseModel):
    title: str
    source: str
    published_at: str
    link: Optional[str] = None
    summary: Optional[str] = None
    sentiment_label: str
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None


class TickerSentiment(BaseModel):
    ticker: str
    name: Optional[str] = None
    overall_sentiment: str
    average_sentiment_score: Optional[float] = None
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    total_articles: int = 0
    sentiment_trend: Optional[str] = None


class SentimentAlert(BaseModel):
    ticker: str
    alert_type: str
    message: str
    triggered_at: str
    severity: str


class SentimentReport(BaseModel):
    generated_at: str
    tickers: list[TickerSentiment] = []
    articles: list[SentimentArticle] = []
    alerts: list[SentimentAlert] = []
    market_mood: str
    summary: str
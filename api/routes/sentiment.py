from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.sentiment_tracker import track_sentiment
from tools.get_news import get_ticker_news, get_broad_market_news

router = APIRouter(prefix="/sentiment", tags=["Sentiment Tracker"])


class SentimentRequest(BaseModel):
    tickers: list[str]


class SentimentResponse(BaseModel):
    success: bool
    data: dict = {}
    error: str = ""


class NewsResponse(BaseModel):
    success: bool
    data: list = []
    error: str = ""


@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment_endpoint(request: SentimentRequest):
    if not request.tickers:
        raise HTTPException(status_code=400, detail="At least one ticker is required")

    if len(request.tickers) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 tickers supported per request")

    tickers = [t.upper().strip() for t in request.tickers]
    result = track_sentiment(tickers)

    if "error" in result:
        return SentimentResponse(success=False, error=result["error"])

    return SentimentResponse(success=True, data=result)


@router.get("/news/{ticker}", response_model=NewsResponse)
async def get_ticker_news_endpoint(ticker: str, limit: int = 10):
    if not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    if limit > 20:
        limit = 20

    news = get_ticker_news(ticker.upper().strip(), limit=limit)
    return NewsResponse(success=True, data=news)


@router.get("/market", response_model=NewsResponse)
async def get_market_news_endpoint(limit: int = 10):
    if limit > 20:
        limit = 20

    news = get_broad_market_news(limit=limit)
    return NewsResponse(success=True, data=news)
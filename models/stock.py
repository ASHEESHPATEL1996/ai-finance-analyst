from pydantic import BaseModel
from typing import Optional


class FinancialMetrics(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    eps: Optional[float] = None
    revenue: Optional[float] = None
    profit_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    return_on_equity: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    analyst_recommendation: Optional[str] = None
    currency: str = None


class NewsItem(BaseModel):
    title: str
    publisher: str
    link: str
    published_at: str
    sentiment: Optional[str] = None


class StockReport(BaseModel):
    ticker: str
    name: str
    generated_at: str
    metrics: FinancialMetrics
    news: list[NewsItem] = []
    analysis: str
    recommendation: str
    confidence: str
    key_risks: list[str] = []
    key_strengths: list[str] = []
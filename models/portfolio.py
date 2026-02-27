from pydantic import BaseModel
from typing import Optional


class Holding(BaseModel):
    ticker: str
    shares: float
    avg_buy_price: Optional[float] = None
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    gain_loss_pct: Optional[float] = None
    weight: Optional[float] = None
    sector: Optional[str] = None


class RiskMetrics(BaseModel):
    sharpe_ratio: Optional[float] = None
    annualized_return: Optional[float] = None
    annualized_volatility: Optional[float] = None
    max_drawdown: Optional[float] = None
    beta: Optional[float] = None
    var_95: Optional[float] = None


class ConcentrationRisk(BaseModel):
    top_holding: str
    top_holding_weight: float
    top_sector: str
    top_sector_weight: float
    is_diversified: bool
    warnings: list[str] = []


class RebalancingSuggestion(BaseModel):
    ticker: str
    action: str
    reason: str
    suggested_weight: Optional[float] = None
    current_weight: Optional[float] = None


class RiskReport(BaseModel):
    generated_at: str
    total_value: float
    holdings: list[Holding] = []
    risk_metrics: RiskMetrics
    concentration_risk: ConcentrationRisk
    rebalancing_suggestions: list[RebalancingSuggestion] = []
    overall_risk_level: str
    summary: str
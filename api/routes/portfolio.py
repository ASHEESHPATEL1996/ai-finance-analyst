from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents.portfolio_risk import analyze_portfolio

router = APIRouter(prefix="/portfolio", tags=["Portfolio Risk"])


class HoldingInput(BaseModel):
    ticker: str
    shares: float
    avg_buy_price: Optional[float] = None


class PortfolioAnalysisRequest(BaseModel):
    holdings: list[HoldingInput]


class PortfolioAnalysisResponse(BaseModel):
    success: bool
    data: dict = {}
    error: str = ""


@router.post("/analyze", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio_endpoint(request: PortfolioAnalysisRequest):
    if not request.holdings:
        raise HTTPException(status_code=400, detail="At least one holding is required")

    if len(request.holdings) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 holdings supported per request")

    holdings = [
        {
            "ticker": h.ticker.upper().strip(),
            "shares": h.shares,
            "avg_buy_price": h.avg_buy_price,
        }
        for h in request.holdings
    ]

    result = analyze_portfolio(holdings)

    if "error" in result:
        return PortfolioAnalysisResponse(success=False, error=result["error"])

    return PortfolioAnalysisResponse(success=True, data=result)
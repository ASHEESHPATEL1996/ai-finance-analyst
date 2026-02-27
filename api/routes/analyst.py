from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.stock_analyst import analyze_stock

router = APIRouter(prefix="/analyst", tags=["Stock Analyst"])


class StockAnalysisRequest(BaseModel):
    ticker: str


class StockAnalysisResponse(BaseModel):
    success: bool
    data: dict = {}
    error: str = ""


@router.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stock_endpoint(request: StockAnalysisRequest):
    if not request.ticker or not request.ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    result = analyze_stock(request.ticker.upper().strip())

    if "error" in result:
        return StockAnalysisResponse(success=False, error=result["error"])

    return StockAnalysisResponse(success=True, data=result)


@router.get("/analyze/{ticker}", response_model=StockAnalysisResponse)
async def analyze_stock_get(ticker: str):
    if not ticker or not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    result = analyze_stock(ticker.upper().strip())

    if "error" in result:
        return StockAnalysisResponse(success=False, error=result["error"])

    return StockAnalysisResponse(success=True, data=result)
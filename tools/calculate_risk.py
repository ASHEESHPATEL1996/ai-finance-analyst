import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def get_returns(ticker: str, period: str = "1y") -> pd.Series:
    stock = yf.Ticker(ticker)
    history = stock.history(period=period)
    if history.empty:
        return pd.Series(dtype=float)
    return history["Close"].pct_change().dropna()


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.05) -> float:
    if returns.empty or returns.std() == 0:
        return 0.0
    excess_returns = returns - (risk_free_rate / 252)
    return round(float((excess_returns.mean() / returns.std()) * np.sqrt(252)), 4)


def calculate_annualized_return(returns: pd.Series) -> float:
    if returns.empty:
        return 0.0
    total_return = (1 + returns).prod() - 1
    years = len(returns) / 252
    if years == 0:
        return 0.0
    return round(float((1 + total_return) ** (1 / years) - 1), 4)


def calculate_annualized_volatility(returns: pd.Series) -> float:
    if returns.empty:
        return 0.0
    return round(float(returns.std() * np.sqrt(252)), 4)


def calculate_max_drawdown(returns: pd.Series) -> float:
    if returns.empty:
        return 0.0
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    return round(float(drawdown.min()), 4)


def calculate_beta(ticker_returns: pd.Series, market_ticker: str = "^GSPC") -> float:
    market = yf.Ticker(market_ticker)
    market_history = market.history(period="1y")
    if market_history.empty or ticker_returns.empty:
        return 1.0
    market_returns = market_history["Close"].pct_change().dropna()
    aligned = pd.concat([ticker_returns, market_returns], axis=1).dropna()
    if aligned.empty or len(aligned) < 10:
        return 1.0
    aligned.columns = ["ticker", "market"]
    covariance = aligned["ticker"].cov(aligned["market"])
    market_variance = aligned["market"].var()
    if market_variance == 0:
        return 1.0
    return round(float(covariance / market_variance), 4)


def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
    if returns.empty:
        return 0.0
    return round(float(np.percentile(returns, (1 - confidence) * 100)), 4)


def calculate_portfolio_risk_metrics(tickers: list[str]) -> dict:
    metrics = {}
    all_returns = {}

    for ticker in tickers:
        returns = get_returns(ticker)
        if not returns.empty:
            all_returns[ticker] = returns
            metrics[ticker] = {
                "sharpe_ratio": calculate_sharpe_ratio(returns),
                "annualized_return": calculate_annualized_return(returns),
                "annualized_volatility": calculate_annualized_volatility(returns),
                "max_drawdown": calculate_max_drawdown(returns),
                "beta": calculate_beta(returns),
                "var_95": calculate_var(returns),
            }

    if not all_returns:
        return {}

    combined_returns = pd.DataFrame(all_returns).mean(axis=1)

    return {
        "per_ticker": metrics,
        "portfolio": {
            "sharpe_ratio": calculate_sharpe_ratio(combined_returns),
            "annualized_return": calculate_annualized_return(combined_returns),
            "annualized_volatility": calculate_annualized_volatility(combined_returns),
            "max_drawdown": calculate_max_drawdown(combined_returns),
            "beta": calculate_beta(combined_returns),
            "var_95": calculate_var(combined_returns),
        }
    }


def calculate_concentration_risk(holdings: list[dict]) -> dict:
    total_value = sum(h.get("current_value", 0) for h in holdings)
    if total_value == 0:
        return {}

    sector_weights = {}
    top_holding = max(holdings, key=lambda h: h.get("current_value", 0))
    top_holding_weight = (top_holding.get("current_value", 0) / total_value) * 100

    for h in holdings:
        sector = h.get("sector", "Unknown")
        weight = (h.get("current_value", 0) / total_value) * 100
        sector_weights[sector] = sector_weights.get(sector, 0) + weight

    top_sector = max(sector_weights, key=sector_weights.get)
    top_sector_weight = sector_weights[top_sector]

    warnings = []
    if top_holding_weight > 30:
        warnings.append(f"{top_holding['ticker']} exceeds 30% of portfolio")
    if top_sector_weight > 40:
        warnings.append(f"{top_sector} sector exceeds 40% of portfolio")
    if len(holdings) < 5:
        warnings.append("Portfolio has fewer than 5 holdings")

    return {
        "top_holding": top_holding["ticker"],
        "top_holding_weight": round(top_holding_weight, 2),
        "top_sector": top_sector,
        "top_sector_weight": round(top_sector_weight, 2),
        "is_diversified": len(warnings) == 0,
        "warnings": warnings,
    }
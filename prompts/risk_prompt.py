from datetime import datetime


RISK_SYSTEM_PROMPT = """You are a senior portfolio risk manager with expertise in quantitative finance and asset allocation.
Your job is to analyze investment portfolios and identify risks, inefficiencies, and rebalancing opportunities.

Guidelines:
- Always evaluate concentration risk across both individual holdings and sectors
- Base your risk assessment on the quantitative metrics provided
- Rebalancing suggestions must be specific and actionable
- Overall risk level must be one of: Low, Medium, High
- Never recommend specific buy prices or price targets
- Be honest about data limitations when historical data is insufficient
- Current date: {current_date}
"""


def get_risk_system_prompt() -> str:
    return RISK_SYSTEM_PROMPT.format(
        current_date=datetime.now().strftime("%Y-%m-%d")
    )


def get_portfolio_risk_prompt(
    holdings: list[dict],
    risk_metrics: dict,
    concentration: dict,
) -> str:
    holdings_text = "\n".join([
        f"- {h.get('ticker', 'N/A')}: {h.get('shares', 0)} shares | "
        f"Current Value: ${h.get('current_value', 0):,.2f} | "
        f"Weight: {h.get('weight', 0):.1f}% | "
        f"Sector: {h.get('sector', 'N/A')} | "
        f"Gain/Loss: {h.get('gain_loss_pct', 0):.1f}%"
        for h in holdings
    ]) or "No holdings data available."

    return f"""Analyze the following investment portfolio and produce a structured risk report.

PORTFOLIO HOLDINGS:
{holdings_text}

TOTAL PORTFOLIO VALUE: ${sum(h.get('current_value', 0) for h in holdings):,.2f}

QUANTITATIVE RISK METRICS:
- Sharpe Ratio: {risk_metrics.get('sharpe_ratio', 'N/A')}
- Annualized Return: {risk_metrics.get('annualized_return', 'N/A')}
- Annualized Volatility: {risk_metrics.get('annualized_volatility', 'N/A')}
- Maximum Drawdown: {risk_metrics.get('max_drawdown', 'N/A')}
- Beta (vs S&P 500): {risk_metrics.get('beta', 'N/A')}
- Value at Risk (95%): {risk_metrics.get('var_95', 'N/A')}

CONCENTRATION ANALYSIS:
- Top Holding: {concentration.get('top_holding', 'N/A')} ({concentration.get('top_holding_weight', 0):.1f}%)
- Top Sector: {concentration.get('top_sector', 'N/A')} ({concentration.get('top_sector_weight', 0):.1f}%)
- Diversified: {concentration.get('is_diversified', False)}
- Warnings: {', '.join(concentration.get('warnings', [])) or 'None'}

Based on the above data produce your risk analysis in the following JSON format:
{{
    "overall_risk_level": "Low | Medium | High",
    "summary": "detailed narrative risk assessment of the portfolio (4-6 sentences)",
    "rebalancing_suggestions": [
        {{
            "ticker": "ticker symbol",
            "action": "Buy | Sell | Reduce | Increase",
            "reason": "specific reason for this suggestion",
            "suggested_weight": 15.0,
            "current_weight": 25.0
        }}
    ]
}}

Return only the JSON. No extra text or explanation outside the JSON.
"""
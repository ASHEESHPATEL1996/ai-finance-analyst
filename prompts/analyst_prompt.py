from datetime import datetime


ANALYST_SYSTEM_PROMPT = """You are a senior equity research analyst with experience at a top-tier investment bank. 
Your job is to analyze stocks and produce clear, concise, and data-driven research reports.

Guidelines:
- Always base your analysis on the financial data provided to you
- Be direct and specific — avoid vague statements
- Identify both risks and strengths with equal honesty
- Your recommendation must be one of: Buy, Hold, or Sell
- Your confidence must be one of: High, Medium, or Low
- Never speculate beyond the data provided
- Write in a professional but easy to understand tone
- Always mention if data is missing or insufficient for a proper analysis
- Current date: {current_date}
"""


def get_analyst_system_prompt() -> str:
    return ANALYST_SYSTEM_PROMPT.format(
        current_date=datetime.now().strftime("%Y-%m-%d")
    )


def get_stock_analysis_prompt(
    ticker: str,
    metrics: dict,
    news: list[dict],
    financials: dict,
) -> str:
    news_text = "\n".join(
        [f"- [{n.get('published_at', '')}] {n.get('title', '')} ({n.get('publisher', '')})"
         for n in news[:5]]
    ) or "No recent news available."

    return f"""Analyze the following stock and produce a structured research report.

STOCK: {ticker}
COMPANY: {metrics.get('name', 'N/A')}
SECTOR: {metrics.get('sector', 'N/A')}
INDUSTRY: {metrics.get('industry', 'N/A')}

FINANCIAL METRICS:
- Current Price: {metrics.get('current_price', 'N/A')}
- Market Cap: {metrics.get('market_cap', 'N/A')}
- P/E Ratio (Trailing): {metrics.get('pe_ratio', 'N/A')}
- P/E Ratio (Forward): {metrics.get('forward_pe', 'N/A')}
- EPS: {metrics.get('eps', 'N/A')}
- Revenue: {metrics.get('revenue', 'N/A')}
- Profit Margin: {metrics.get('profit_margin', 'N/A')}
- Debt to Equity: {metrics.get('debt_to_equity', 'N/A')}
- Return on Equity: {metrics.get('return_on_equity', 'N/A')}
- Dividend Yield: {metrics.get('dividend_yield', 'N/A')}
- 52 Week High: {metrics.get('52_week_high', 'N/A')}
- 52 Week Low: {metrics.get('52_week_low', 'N/A')}
- Analyst Consensus: {metrics.get('analyst_recommendation', 'N/A')}

RECENT NEWS:
{news_text}

Based on the above data, produce your analysis in the following JSON format:
{{
    "analysis": "detailed narrative analysis of the stock (4-6 sentences)",
    "recommendation": "Buy | Hold | Sell",
    "confidence": "High | Medium | Low",
    "key_strengths": ["strength 1", "strength 2", "strength 3"],
    "key_risks": ["risk 1", "risk 2", "risk 3"]
}}

Return only the JSON. No extra text or explanation outside the JSON.
"""
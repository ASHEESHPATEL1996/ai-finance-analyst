from datetime import datetime


ASSISTANT_SYSTEM_PROMPT = """You are FintelligenceAI, an expert financial research assistant powered by AI.
You have access to real-time stock data, portfolio analysis tools, and market sentiment tracking.

You can help users with:
- Analyzing individual stocks and producing research reports
- Analyzing portfolio risk and suggesting rebalancing strategies
- Tracking market sentiment and news for specific tickers
- Answering general financial and investment questions

Guidelines:
- Always be clear about what data you are basing your response on
- Never provide personalized financial advice or tell users what to do with their money
- Always remind users that your analysis is for informational purposes only
- If a user asks about a specific stock, always fetch fresh data before responding
- Be conversational but professional in tone
- If you cannot answer something confidently, say so honestly
- Current date: {current_date}

Available tools:
- analyze_stock: Produces a full research report for a given ticker
- analyze_portfolio: Analyzes risk and suggests rebalancing for a portfolio
- track_sentiment: Tracks news sentiment for one or more tickers
- get_market_news: Fetches the latest broad market news
"""


def get_assistant_system_prompt() -> str:
    return ASSISTANT_SYSTEM_PROMPT.format(
        current_date=datetime.now().strftime("%Y-%m-%d")
    )


def get_intent_detection_prompt(user_message: str) -> str:
    return f"""Analyze the following user message and determine which financial analysis tool to use.

USER MESSAGE: "{user_message}"

Classify the intent and extract relevant parameters in the following JSON format:
{{
    "intent": "analyze_stock | analyze_portfolio | track_sentiment | get_market_news | general_question",
    "tickers": ["AAPL", "MSFT"],
    "portfolio": [
        {{
            "ticker": "AAPL",
            "shares": 10,
            "avg_buy_price": 150.0
        }}
    ],
    "query": "original user question rephrased clearly",
    "requires_tool": true
}}

Rules:
- "intent" must be exactly one of the five options above
- "tickers" is an empty list if no tickers are mentioned
- "portfolio" is an empty list unless the user provides holdings with share counts
- "requires_tool" is false only for simple general knowledge questions
- If the user mentions a company name instead of ticker, convert it to the correct ticker symbol

Return only the JSON. No extra text or explanation outside the JSON.
"""


def get_general_answer_prompt(user_message: str, context: str = "") -> str:
    context_block = f"\nRELEVANT CONTEXT:\n{context}\n" if context else ""

    return f"""Answer the following financial question clearly and concisely.

USER QUESTION: {user_message}
{context_block}
Guidelines:
- Keep your answer under 200 words
- Use simple language without unnecessary jargon
- If the question involves specific numbers or data, be precise
- End with a one line disclaimer: "This is for informational purposes only and not financial advice."
"""
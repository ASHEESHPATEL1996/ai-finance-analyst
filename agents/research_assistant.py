import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from core.llm_client import get_llm
from agents.stock_analyst import analyze_stock
from agents.portfolio_risk import analyze_portfolio
from agents.sentiment_tracker import track_sentiment
from tools.get_news import get_broad_market_news
from tools.get_stock_data import validate_ticker
from prompts.assistant_prompt import (
    get_assistant_system_prompt,
    get_intent_detection_prompt,
    get_general_answer_prompt,
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class AssistantState(TypedDict):
    user_message: str
    chat_history: list[dict]
    intent: Optional[str]
    tickers: Optional[list[str]]
    portfolio: Optional[list[dict]]
    tool_result: Optional[dict]
    llm_response: Optional[str]
    error: Optional[str]


def detect_intent_node(state: AssistantState) -> AssistantState:
    try:
        llm = get_llm(temperature=0.0)
        prompt = get_intent_detection_prompt(state["user_message"])
        response = llm.invoke([HumanMessage(content=prompt)])

        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        return {
            **state,
            "intent": parsed.get("intent", "general_question"),
            "tickers": parsed.get("tickers", []),
            "portfolio": parsed.get("portfolio", []),
        }
    except Exception as e:
        return {**state, "intent": "general_question", "tickers": [], "portfolio": []}


def route_to_tool_node(state: AssistantState) -> AssistantState:
    intent = state.get("intent", "general_question")
    tickers = state.get("tickers", [])
    portfolio = state.get("portfolio", [])

    try:
        if intent == "analyze_stock" and tickers:
            ticker = tickers[0]
            if not validate_ticker(ticker):
                return {**state, "error": f"Could not find stock data for {ticker}. Please check the ticker symbol."}
            result = analyze_stock(ticker)
            return {**state, "tool_result": {"type": "stock_report", "data": result}}

        elif intent == "analyze_portfolio" and portfolio:
            result = analyze_portfolio(portfolio)
            return {**state, "tool_result": {"type": "portfolio_report", "data": result}}

        elif intent == "track_sentiment" and tickers:
            result = track_sentiment(tickers)
            return {**state, "tool_result": {"type": "sentiment_report", "data": result}}

        elif intent == "get_market_news":
            news = get_broad_market_news(limit=10)
            return {**state, "tool_result": {"type": "market_news", "data": news}}

        else:
            return {**state, "tool_result": None}

    except Exception as e:
        return {**state, "error": f"Tool execution failed: {str(e)}"}


def generate_response_node(state: AssistantState) -> AssistantState:
    if state.get("error"):
        return {**state, "llm_response": f"I encountered an issue: {state['error']}"}

    try:
        llm = get_llm(temperature=0.3)
        tool_result = state.get("tool_result")
        chat_history = state.get("chat_history", [])

        messages = [SystemMessage(content=get_assistant_system_prompt())]

        for msg in chat_history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        if tool_result:
            context = json.dumps(tool_result["data"], indent=2, default=str)
            user_content = f"""The user asked: {state['user_message']}

Here is the data retrieved from our analysis tools:
{context}

Based on this data, provide a clear and helpful response to the user.
Keep your response conversational, highlight the most important findings,
and remind them this is for informational purposes only."""
        else:
            user_content = get_general_answer_prompt(state["user_message"])

        messages.append(HumanMessage(content=user_content))
        response = llm.invoke(messages)

        return {**state, "llm_response": response.content}
    except Exception as e:
        return {**state, "llm_response": f"I'm sorry, I was unable to generate a response. Please try again."}


def build_assistant_graph() -> StateGraph:
    graph = StateGraph(AssistantState)

    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("route_to_tool", route_to_tool_node)
    graph.add_node("generate_response", generate_response_node)

    graph.set_entry_point("detect_intent")
    graph.add_edge("detect_intent", "route_to_tool")
    graph.add_edge("route_to_tool", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


def chat(user_message: str, chat_history: list[dict] = []) -> dict:
    graph = build_assistant_graph()
    result = graph.invoke({
        "user_message": user_message,
        "chat_history": chat_history,
    })
    return {
        "response": result.get("llm_response", ""),
        "intent": result.get("intent", "general_question"),
        "tool_result": result.get("tool_result"),
        "error": result.get("error"),
    }
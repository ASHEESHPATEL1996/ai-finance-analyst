import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    for key, value in st.secrets.items():
        os.environ.setdefault(key.upper(), str(value))
except Exception:
    pass

from agents.stock_analyst import analyze_stock
from agents.portfolio_risk import analyze_portfolio
from agents.sentiment_tracker import track_sentiment
from agents.research_assistant import chat
from tools.search_ticker import find_ticker

st.set_page_config(
    page_title="Fintelligence AI",
    layout="wide",
)


def api_post(endpoint: str, payload: dict) -> dict:
    try:
        if endpoint == "/analyst/analyze":
            data = analyze_stock(payload["ticker"])
        elif endpoint == "/portfolio/analyze":
            data = analyze_portfolio(payload["holdings"])
        elif endpoint == "/sentiment/analyze":
            data = track_sentiment(payload["tickers"])
        elif endpoint == "/assistant/chat":
            result = chat(payload["message"], payload.get("chat_history", []))
            return {
                "success": True,
                "response": result.get("response", ""),
                "intent": result.get("intent", ""),
                "tool_result": result.get("tool_result"),
            }
        else:
            return {"success": False, "error": "Unknown endpoint"}

        if "error" in data:
            return {"success": False, "error": data["error"]}
        return {"success": True, "data": data}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_currency_symbol(currency: str) -> str:
    if not currency:
        return "$"
    symbols = {
        "USD": "$", "INR": "₹", "EUR": "€",
        "GBP": "£", "JPY": "¥", "CAD": "CA$",
        "AUD": "A$", "HKD": "HK$", "SGD": "S$",
    }
    return symbols.get(currency, currency + " ")


def format_large_number(value, symbol: str = "$") -> str:
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"{symbol}{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{symbol}{value / 1_000_000:.2f}M"
    return f"{symbol}{value:,.2f}"


with st.sidebar:
    st.title("Fintelligence AI")
    st.caption("AI-Powered Investment Research Platform")
    st.divider()

    page = st.radio(
        "Navigate",
        ["Stock Analyst", "Portfolio Risk", "Sentiment Tracker", "AI Assistant"],
        label_visibility="collapsed",
    )

    st.divider()
    st.success("Running", icon="🟢")
    st.caption("For informational purposes only. Not financial advice.")


if page == "Stock Analyst":
    st.title("Stock Analyst")
    st.caption("AI-powered equity research with Buy / Hold / Sell recommendations")
    st.divider()

    with st.expander("Don't know the ticker? Search by company name"):
        company_query = st.text_input("Company Name", placeholder="e.g. Reliance Industries, Tata Motors, Apple")
        search_btn = st.button("Search Ticker", type="secondary")

        if search_btn and company_query:
            with st.spinner("Searching..."):
                search_results = find_ticker(company_query)

            if not search_results or "error" in search_results[0]:
                st.warning("No results found. Try a different company name.")
            else:
                st.write("**Results:**")
                for r in search_results:
                    col1, col2, col3 = st.columns([2, 3, 2])
                    col1.code(r.get("ticker", ""))
                    col2.write(r.get("name", ""))
                    currency = r.get("currency", "")
                    currency_text = f"💱 {currency}" if currency and currency != "Unknown" else ""
                    col3.write(r.get("exchange", "") + f" · {r.get('country', '')} {currency_text}")

    ticker_input = st.text_input("Enter Ticker Symbol", placeholder="e.g. AAPL, RELIANCE.NS, TCS.NS")
    analyze_btn = st.button("Analyze Stock", type="primary")

    if analyze_btn and ticker_input:
        with st.spinner(f"Analyzing {ticker_input.upper()}..."):
            result = api_post("/analyst/analyze", {"ticker": ticker_input})

        if not result.get("success"):
            st.error(result.get("error", "Analysis failed"))
        else:
            data = result["data"]
            metrics = data.get("metrics", {})

            currency = metrics.get("currency") or "USD"
            symbol = get_currency_symbol(currency)

            if currency != "USD":
                st.info(f"This stock trades in **{currency}** ({symbol}). All prices shown in {currency}.")

            st.divider()
            col_name, col_price, col_rec, col_conf = st.columns(4)
            col_name.metric("Company", data.get("name", "N/A"))
            col_price.metric("Current Price", f"{symbol}{metrics.get('current_price', 'N/A')}")
            col_rec.metric("Recommendation", data.get("recommendation", "N/A"))
            col_conf.metric("Confidence", data.get("confidence", "N/A"))

            tab_overview, tab_analysis, tab_news = st.tabs(["Overview", "Analysis", "News"])

            with tab_overview:
                st.subheader("Financial Metrics")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Market Cap", format_large_number(metrics.get("market_cap"), symbol))
                c2.metric("P/E Ratio", metrics.get("pe_ratio", "N/A"))
                c3.metric("Forward P/E", metrics.get("forward_pe", "N/A"))
                c4.metric("EPS", f"{symbol}{metrics.get('eps', 'N/A')}" if metrics.get("eps") else "N/A")

                c5, c6, c7, c8 = st.columns(4)
                c5.metric("52W High", f"{symbol}{metrics.get('week_52_high', 'N/A')}")
                c6.metric("52W Low", f"{symbol}{metrics.get('week_52_low', 'N/A')}")
                c7.metric("ROE", metrics.get("return_on_equity", "N/A"))
                c8.metric("Profit Margin", metrics.get("profit_margin", "N/A"))

                c9, c10, c11 = st.columns(3)
                c9.metric("Sector", metrics.get("sector", "N/A"))
                c10.metric("Analyst Consensus", metrics.get("analyst_recommendation", "N/A"))
                c11.metric("Currency", f"{currency} ({symbol})")

            with tab_analysis:
                st.subheader("AI Analysis")
                st.info(data.get("analysis", "No analysis available."))

                col_s, col_r = st.columns(2)
                with col_s:
                    st.subheader("Key Strengths")
                    for strength in data.get("key_strengths", []):
                        st.success(strength)

                with col_r:
                    st.subheader("Key Risks")
                    for risk in data.get("key_risks", []):
                        st.error(risk)

            with tab_news:
                st.subheader("Recent News")
                for news_item in data.get("news", [])[:5]:
                    with st.expander(news_item.get("title", "No title")):
                        st.write(f"**Publisher:** {news_item.get('publisher', 'N/A')}")
                        st.write(f"**Published:** {news_item.get('published_at', 'N/A')}")
                        st.write(f"**Sentiment:** {news_item.get('sentiment', 'N/A')}")
                        if news_item.get("link"):
                            st.link_button("Read Article", news_item["link"])


elif page == "Portfolio Risk":
    st.title("Portfolio Risk Analyzer")
    st.caption("Quantitative risk metrics and rebalancing suggestions for your holdings")
    st.divider()

    st.subheader("Enter Your Holdings")
    st.caption("Format: TICKER, SHARES, AVG_BUY_PRICE (one per line). Avg buy price is optional.")

    holdings_text = st.text_area(
        "Holdings",
        placeholder="AAPL, 10, 150.00\nRELIANCE.NS, 5, 2800.00\nTCS.NS, 3, 3500.00",
        height=180,
        label_visibility="collapsed",
    )

    analyze_btn = st.button("Analyze Portfolio", type="primary")

    if analyze_btn and holdings_text:
        holdings = []
        for line in holdings_text.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                try:
                    holding = {"ticker": parts[0].upper(), "shares": float(parts[1])}
                    if len(parts) >= 3:
                        holding["avg_buy_price"] = float(parts[2])
                    holdings.append(holding)
                except ValueError:
                    continue

        if not holdings:
            st.error("No valid holdings found. Please check the format.")
        else:
            with st.spinner("Analyzing portfolio risk..."):
                result = api_post("/portfolio/analyze", {"holdings": holdings})

            if not result.get("success"):
                st.error(result.get("error", "Analysis failed"))
            else:
                data = result["data"]
                risk_metrics = data.get("risk_metrics", {})
                concentration = data.get("concentration_risk", {})

                mixed_currencies = set()
                for h in data.get("holdings", []):
                    c = h.get("currency", "USD")
                    if c:
                        mixed_currencies.add(c)

                if len(mixed_currencies) > 1:
                    st.warning(f"Your portfolio contains multiple currencies: {', '.join(mixed_currencies)}. Total value comparison may not be accurate.")

                st.divider()
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Portfolio Value", f"{data.get('total_value', 0):,.2f}")
                c2.metric("Overall Risk Level", data.get("overall_risk_level", "N/A"))
                c3.metric("Diversified", "Yes ✓" if concentration.get("is_diversified") else "No ✗")

                tab_metrics, tab_holdings, tab_rebalance, tab_summary = st.tabs([
                    "Risk Metrics", "Holdings", "Rebalancing", "Summary"
                ])

                with tab_metrics:
                    st.subheader("Quantitative Risk Metrics")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Sharpe Ratio", risk_metrics.get("sharpe_ratio", "N/A"))
                    m2.metric("Annualized Return", f"{(risk_metrics.get('annualized_return') or 0) * 100:.1f}%")
                    m3.metric("Annualized Volatility", f"{(risk_metrics.get('annualized_volatility') or 0) * 100:.1f}%")

                    m4, m5, m6 = st.columns(3)
                    m4.metric("Max Drawdown", f"{(risk_metrics.get('max_drawdown') or 0) * 100:.1f}%")
                    m5.metric("Beta vs S&P 500", risk_metrics.get("beta", "N/A"))
                    m6.metric("VaR 95%", f"{(risk_metrics.get('var_95') or 0) * 100:.1f}%")

                    st.subheader("Concentration Risk")
                    cc1, cc2 = st.columns(2)
                    cc1.metric("Top Holding", f"{concentration.get('top_holding', 'N/A')} ({concentration.get('top_holding_weight', 0):.1f}%)")
                    cc2.metric("Top Sector", f"{concentration.get('top_sector', 'N/A')} ({concentration.get('top_sector_weight', 0):.1f}%)")

                    for warning in concentration.get("warnings", []):
                        st.warning(warning)

                with tab_holdings:
                    st.subheader("Holdings Breakdown")
                    for h in data.get("holdings", []):
                        h_currency = h.get("currency", "USD")
                        h_symbol = get_currency_symbol(h_currency)
                        with st.expander(f"{h.get('ticker')} — {h_symbol}{h.get('current_value', 0):,.2f} ({h.get('weight', 0):.1f}% weight)"):
                            hc1, hc2, hc3, hc4 = st.columns(4)
                            hc1.metric("Shares", h.get("shares"))
                            hc2.metric("Current Price", f"{h_symbol}{h.get('current_price', 0):,.2f}")
                            hc3.metric("Avg Buy Price", f"{h_symbol}{h.get('avg_buy_price', 0):,.2f}")
                            hc4.metric("Gain / Loss", f"{h.get('gain_loss_pct', 0):.1f}%")
                            st.caption(f"Sector: {h.get('sector', 'N/A')} · Currency: {h_currency} ({h_symbol})")

                with tab_rebalance:
                    st.subheader("Rebalancing Suggestions")
                    suggestions = data.get("rebalancing_suggestions", [])
                    if not suggestions:
                        st.info("No rebalancing suggestions at this time.")
                    else:
                        for s in suggestions:
                            action = s.get("action", "")
                            msg = f"**{action} {s.get('ticker')}** — {s.get('reason')} | Current: {s.get('current_weight', 0):.1f}% → Suggested: {s.get('suggested_weight', 0):.1f}%"
                            if action in ["Buy", "Increase"]:
                                st.success(msg)
                            else:
                                st.error(msg)

                with tab_summary:
                    st.subheader("Risk Summary")
                    st.info(data.get("summary", "No summary available."))


elif page == "Sentiment Tracker":
    st.title("Sentiment Tracker")
    st.caption("Real-time news sentiment analysis and market mood detection")
    st.divider()

    tickers_input = st.text_input("Enter Tickers", placeholder="Comma separated — e.g. AAPL, RELIANCE.NS, TCS.NS")
    sentiment_btn = st.button("Track Sentiment", type="primary")

    if sentiment_btn and tickers_input:
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        if len(tickers) > 5:
            st.warning("Maximum 5 tickers supported. Using first 5.")
            tickers = tickers[:5]

        with st.spinner("Fetching and analyzing sentiment..."):
            result = api_post("/sentiment/analyze", {"tickers": tickers})

        if not result.get("success"):
            st.error(result.get("error", "Analysis failed"))
        else:
            data = result["data"]
            st.divider()

            st.metric("Overall Market Mood", data.get("market_mood", "Neutral"))
            st.info(data.get("summary", ""))

            if data.get("alerts"):
                st.subheader("Alerts")
                for alert in data["alerts"]:
                    severity = alert.get("severity", "Low")
                    msg = f"**[{severity}] {alert.get('ticker')} — {alert.get('alert_type')}**: {alert.get('message')}"
                    if severity == "High":
                        st.error(msg)
                    elif severity == "Medium":
                        st.warning(msg)
                    else:
                        st.info(msg)

            tab_breakdown, tab_articles = st.tabs(["Ticker Breakdown", "Recent Articles"])

            with tab_breakdown:
                st.subheader("Sentiment Breakdown by Ticker")
                for ts in data.get("tickers", []):
                    with st.expander(f"{ts.get('ticker')} — {ts.get('overall_sentiment', 'N/A')} | Trend: {ts.get('sentiment_trend', 'Stable')}"):
                        tc1, tc2, tc3, tc4 = st.columns(4)
                        tc1.metric("Overall", ts.get("overall_sentiment", "N/A"))
                        tc2.metric("Trend", ts.get("sentiment_trend", "Stable"))
                        tc3.metric("Avg Score", f"{ts.get('average_sentiment_score', 0):.2f}")
                        tc4.metric("Total Articles", ts.get("total_articles", 0))

                        bc1, bc2, bc3 = st.columns(3)
                        bc1.metric("Bullish", ts.get("bullish_count", 0))
                        bc2.metric("Neutral", ts.get("neutral_count", 0))
                        bc3.metric("Bearish", ts.get("bearish_count", 0))

                        total = ts.get("total_articles", 1) or 1
                        bull_pct = ts.get("bullish_count", 0) / total
                        st.progress(bull_pct, text=f"Bullish ratio: {bull_pct * 100:.0f}%")

            with tab_articles:
                st.subheader("Recent Articles")
                for article in data.get("articles", [])[:10]:
                    with st.expander(article.get("title", "No title")):
                        ac1, ac2, ac3 = st.columns(3)
                        ac1.write(f"**Source:** {article.get('source', 'N/A')}")
                        ac2.write(f"**Published:** {article.get('published_at', 'N/A')}")
                        ac3.write(f"**Sentiment:** {article.get('sentiment_label', 'N/A')}")
                        if article.get("summary"):
                            st.caption(article["summary"])
                        if article.get("link"):
                            st.link_button("Read Article", article["link"])


elif page == "AI Assistant":
    st.title("AI Research Assistant")
    st.caption("Conversational financial research — ask anything about stocks, portfolios, or markets")
    st.divider()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "display_history" not in st.session_state:
        st.session_state.display_history = []

    for msg in st.session_state.display_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if not st.session_state.display_history:
        st.info("💡 Try asking: *Analyze AAPL stock* · *Analyze Reliance Industries* · *Track sentiment for TCS.NS*")

    user_input = st.chat_input("Ask anything about stocks, portfolios, or markets...")

    if user_input:
        st.session_state.display_history.append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            result = api_post("/assistant/chat", {
                "message": user_input,
                "chat_history": st.session_state.chat_history,
            })

        response_text = (
            result.get("response", "")
            if result.get("success")
            else f"Error: {result.get('error', 'Unknown error')}"
        )

        st.session_state.display_history.append({"role": "assistant", "content": response_text})
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})

        st.rerun()

    if st.session_state.display_history:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.display_history = []
            st.rerun()
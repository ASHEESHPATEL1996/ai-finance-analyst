### AI-Powered Investment Research Platform
This is a production-grade **multi-agent investment research platform** that automates equity analysis, portfolio risk management, and market sentiment tracking. Built with LangGraph for agentic orchestration and Groq for ultra-fast LLM inference, it delivers institutional-quality financial research in seconds.

---

## Live Demo

👉 [fintelligence.streamlit.app](https://fintelligence.streamlit.app)

---

## Features

### stock Analyst Agent
- AI-generated **Buy / Hold / Sell** recommendations with confidence levels
- Real-time financial metrics — P/E ratio, EPS, market cap, ROE, profit margins
- 52-week high/low tracking and analyst consensus
- Key strengths and risk identification
- Multi-currency support — USD, INR, EUR, GBP, JPY and more
- Latest news with sentiment labels per article

### Portfolio Risk Agent
- Quantitative risk metrics — **Sharpe ratio, beta, VaR (95%), max drawdown**
- Annualized return and volatility calculations
- Concentration risk detection across holdings and sectors
- AI-generated rebalancing suggestions with specific weight targets
- Multi-currency portfolio support with cross-currency warnings

### Sentiment Tracker Agent
- Real-time news sentiment analysis across multiple tickers simultaneously
- Bullish / Bearish / Neutral classification with scoring
- Sentiment trend detection — Improving / Declining / Stable
- Automated alerts for sudden sentiment shifts
- Overall market mood assessment
- Aggregated from Yahoo Finance, Alpha Vantage, and Google News RSS

### AI Research Assistant
- Conversational interface for financial research queries
- Automatic intent detection — routes to the right agent automatically
- Multi-turn conversation with context memory
- Handles natural language — "Analyze Apple" works the same as "Analyze AAPL"
- Answers general financial questions without triggering unnecessary API calls

### Ticker Search
- Search any stock by company name — no need to know the ticker
- Returns exchange, country, and currency for each result
- Full support for Indian stocks (NSE/BSE), US, UK, European, and Asian markets

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Streamlit Frontend              │
└─────────────────────┬───────────────────────┘
                      │
         ┌────────────▼────────────┐
         │   Research Assistant    │  ← Master Orchestrator
         │   (LangGraph Agent)     │
         └──┬──────┬──────┬───────┘
            │      │      │
   ┌────────▼─┐ ┌──▼────┐ ┌▼──────────────┐
   │  Stock   │ │  Risk │ │   Sentiment   │
   │ Analyst  │ │ Agent │ │    Tracker    │
   └────────┬─┘ └──┬────┘ └┬──────────────┘
            │      │       │
   ┌────────▼──────▼───────▼──────────────┐
   │              Tools Layer              │
   │  get_stock_data · calculate_risk ·   │
   │  get_news · classify_sentiment       │
   └────────────────┬─────────────────────┘
                    │
   ┌────────────────▼─────────────────────┐
   │              Core Layer              │
   │  yFinance · Alpha Vantage · Groq     │
   │  Yahoo RSS · Google News RSS         │
   └──────────────────────────────────────┘
```

Each agent is a **LangGraph StateGraph** with dedicated nodes:

| Agent | Nodes |
|---|---|
| Stock Analyst | validate → fetch_data → calculate_metrics → analyze → parse_output |
| Portfolio Risk | enrich_holdings → calculate_risk → analyze → parse_output |
| Sentiment Tracker | fetch_news → aggregate_sentiment → analyze_ticker → analyze_market → parse_output |
| Research Assistant | detect_intent → route_to_tool → generate_response |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq (Llama 3.1 8B Instant) |
| Agent Framework | LangGraph + LangChain |
| Financial Data | yFinance + Alpha Vantage |
| News & Sentiment | Yahoo Finance RSS + Google News RSS |
| Backend API | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Data Validation | Pydantic v2 |
| Risk Calculations | NumPy + Pandas |
| Web Scraping | BeautifulSoup4 + lxml |
| Config Management | pydantic-settings + python-dotenv |

### LLM Flexibility
The platform supports **three LLM providers** — switch with a single `.env` change:
```bash
LLM_PROVIDER=groq       # Llama 3.1 8B Instant (default, free)
LLM_PROVIDER=openai     # GPT-4o Mini
LLM_PROVIDER=anthropic  # Claude Haiku
```

---

## Project Structure

```
fintelligence/
├── main.py                
├── requirements.txt
├── .env
│
├── core/
│   ├── config.py                  # Settings and env management
│   ├── llm_client.py              # Multi-provider LLM factory
│   ├── financial_data.py          # yFinance + Alpha Vantage wrapper
│   └── web_search.py              # RSS news scraper
│
├── agents/                        # LangGraph agents
│   ├── stock_analyst.py           # Feature 1 — Buy/Hold/Sell reports
│   ├── portfolio_risk.py          # Feature 2 — Risk + rebalancing
│   ├── sentiment_tracker.py       # Feature 4 — News sentiment
│   └── research_assistant.py      # Feature 5 — Master orchestrator
│
├── tools/                         # Reusable tool functions
│   ├── get_stock_data.py          # Unified stock data fetcher
│   ├── get_news.py                # Unified news fetcher
│   ├── calculate_risk.py          # Sharpe, beta, VaR, drawdown
│   ├── classify_sentiment.py      # Sentiment classification logic
│   └── search_ticker.py           # Company name to ticker search
│
├── models/                        # Pydantic data models
│   ├── stock.py                   # StockReport, FinancialMetrics
│   ├── portfolio.py               # RiskReport, Holding
│   └── sentiment.py               # SentimentReport, SentimentArticle
│
├── prompts/                       # LLM prompt templates
│   ├── analyst_prompt.py
│   ├── risk_prompt.py
│   ├── sentiment_prompt.py
│   └── assistant_prompt.py
│
├── api/                           # FastAPI routes
│   ├── middleware.py              # CORS + error handling
│   └── routes/
│       ├── analyst.py
│       ├── portfolio.py
│       ├── sentiment.py
│       └── assistant.py
│
└── frontend/
    └── app.py                     # Streamlit dashboard
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Groq API key — [console.groq.com](https://console.groq.com) (free)
- Alpha Vantage API key — [alphavantage.co](https://www.alphavantage.co) (free)

### Installation

```bash
# Clone the repository
git clone https://github.com/ASHEESHPATEL1996/ai-finance-analyst
cd ai-finance-analyst

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   
.venv\Scripts\activate      

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
```

### Run Locally

```bash
# Option 1 — Streamlit only (no backend needed)
streamlit run frontend/app.py

# Option 2 — Full stack
# Terminal 1
python main.py

# Terminal 2
streamlit run frontend/app.py
```

Open → **http://localhost:8501**

---

## Deployment

### Streamlit Cloud (Frontend)

1. Push your repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set **Main file** to `frontend/app.py`
4. Add secrets in **Settings → Secrets**:

```toml
GROQ_API_KEY = "your_groq_key"
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_key"
LLM_PROVIDER = "groq"
APP_ENV = "production"
```
## Example Queries

| Query | Agent Triggered |
|---|---|
| "Analyze AAPL" | Stock Analyst |
| "Analyze Reliance Industries" | Stock Analyst |
| "What is the risk in my portfolio: AAPL 10, MSFT 5" | Portfolio Risk |
| "Track sentiment for TSLA and NVDA" | Sentiment Tracker |
| "What is a Sharpe ratio?" | General Answer |
| "What are the risks of a tech-heavy portfolio?" | General Answer |

---


## Disclaimer

Fintelligence AI is for **informational and educational purposes only**. Nothing on this platform constitutes financial advice, investment advice, or a recommendation to buy or sell any security. Always consult a qualified financial advisor before making investment decisions.

---

## Contributing

Pull requests are welcome. For major changes please open an issue first to discuss what you would like to change.

---
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def search_ticker_yahoo(query: str) -> list[dict]:
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": query,
            "quotesCount": 8,
            "newsCount": 0,
            "listsCount": 0,
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()
        results = []
        for quote in data.get("quotes", []):
            symbol = quote.get("symbol", "")
            name = quote.get("longname") or quote.get("shortname", "")
            exchange = quote.get("exchange", "")
            quote_type = quote.get("quoteType", "")
            score = quote.get("score", 0)

            if quote_type not in ("EQUITY", "ETF", "MUTUALFUND"):
                continue

            results.append({
                "ticker": symbol,
                "name": name,
                "exchange": exchange,
                "type": quote_type,
                "score": score,
                "country": detect_country_from_exchange(exchange),
                "currency": detect_currency_from_exchange(exchange),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    except Exception as e:
        return [{"error": str(e)}]


def search_ticker_google(query: str) -> list[dict]:
    try:
        search_query = f"{query} stock ticker symbol site:finance.yahoo.com"
        url = f"https://news.google.com/rss/search?q={search_query.replace(' ', '+')}&hl=en-US"
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, "lxml-xml")
        items = soup.find_all("item")[:5]

        results = []
        for item in items:
            title = item.find("title").get_text(strip=True) if item.find("title") else ""
            tickers_found = re.findall(r'\b[A-Z]{1,5}(?:\.[A-Z]{1,2})?\b', title)
            for ticker in tickers_found:
                if len(ticker) >= 2:
                    results.append({
                        "ticker": ticker,
                        "name": title,
                        "exchange": "Unknown",
                        "type": "EQUITY",
                        "source": "google_news",
                        "country": "Unknown",
                        "currency": "Unknown",
                    })

        return results

    except Exception as e:
        return []


def detect_country_from_exchange(exchange: str) -> str:
    exchange_map = {
        "NSE": "India",
        "BSE": "India",
        "NMS": "USA",
        "NYQ": "USA",
        "NGM": "USA",
        "PCX": "USA",
        "LSE": "UK",
        "TSX": "Canada",
        "ASX": "Australia",
        "HKG": "Hong Kong",
        "TYO": "Japan",
        "SGX": "Singapore",
        "FRA": "Germany",
        "PAR": "France",
    }
    return exchange_map.get(exchange.upper(), "Unknown")


def detect_currency_from_exchange(exchange: str) -> str:
    currency_map = {
        "NSE": "INR",
        "BSE": "INR",
        "NMS": "USD",
        "NYQ": "USD",
        "NGM": "USD",
        "PCX": "USD",
        "LSE": "GBP",
        "TSX": "CAD",
        "ASX": "AUD",
        "HKG": "HKD",
        "TYO": "JPY",
        "SGX": "SGD",
        "FRA": "EUR",
        "PAR": "EUR",
    }
    return currency_map.get(exchange.upper(), "Unknown")


def find_ticker(query: str) -> list[dict]:
    yahoo_results = search_ticker_yahoo(query)
    valid = [r for r in yahoo_results if "error" not in r]

    if valid:
        return valid[:5]

    google_results = search_ticker_google(query)
    return google_results[:5]


def get_best_ticker_match(query: str) -> dict | None:
    results = find_ticker(query)
    if not results or "error" in results[0]:
        return None
    return results[0]
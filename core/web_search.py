import requests
from bs4 import BeautifulSoup
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _parse_rss(url: str, limit: int) -> list[dict]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, "lxml-xml")
        items = soup.find_all("item")[:limit]
        results = []
        for item in items:
            results.append({
                "title": item.find("title").get_text(strip=True) if item.find("title") else "",
                "link": item.find("link").get_text(strip=True) if item.find("link") else "",
                "published_at": item.find("pubDate").get_text(strip=True) if item.find("pubDate") else "",
                "source": item.find("source").get_text(strip=True) if item.find("source") else "",
                "summary": item.find("description").get_text(strip=True) if item.find("description") else "",
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


def get_yahoo_finance_news(ticker: str, limit: int = 10) -> list[dict]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    return _parse_rss(url, limit)


def get_google_finance_news(query: str, limit: int = 10) -> list[dict]:
    formatted_query = query.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={formatted_query}+finance&hl=en-US&gl=US&ceid=US:en"
    return _parse_rss(url, limit)


def get_market_news(limit: int = 10) -> list[dict]:
    url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC&region=US&lang=en-US"
    return _parse_rss(url, limit)


def get_sector_news(sector: str, limit: int = 10) -> list[dict]:
    return get_google_finance_news(f"{sector} sector stocks", limit)
"""Yahoo Finance News fetcher"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Yahoo Finance RSS feeds
YAHOO_RSS_URL = "https://finance.yahoo.com/topic/stock-market/"
YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"

def fetch_yahoo_news(symbol: str, days: int = 3, user_agent: str = "news_service/1.0") -> List[Dict]:
    """Fetch Yahoo Finance news for a symbol"""
    results = []
    
    try:
        # Use Yahoo Finance search API
        params = {
            "q": f"{symbol} stock",
            "quotesCount": 5,
            "newsCount": 15,
            "quotesQueryId": "tss_match_phrase_query",
            "newsQueryId": "news_cie_vespa",
        }
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json"
        }
        
        response = requests.get(YAHOO_SEARCH_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        news_items = data.get("news", [])
        
        for item in news_items[:15]:
            title = item.get("title", "")
            link = item.get("link", "")
            pub_ts = item.get("providerPublishTime", 0)
            publisher = item.get("publisher", "")
            
            pub_date = None
            if pub_ts:
                pub_date = datetime.fromtimestamp(pub_ts)
            
            if pub_date and pub_date < datetime.now() - timedelta(days=days):
                continue
            
            summary = item.get("summary", "")[:200] if item.get("summary") else title[:200]
            
            results.append({
                "symbol": symbol.upper(),
                "title": title[:500],
                "url": link,
                "source": "yahoo_finance",
                "evidence_type": "media",
                "category": "company_news",
                "published_at": pub_date,
                "origin_publisher": publisher,
                "summary_text": summary
            })
        
        logger.info(f"Fetched {len(results)} Yahoo Finance items for {symbol}")
        
    except Exception as e:
        logger.error(f"Yahoo Finance fetch failed for {symbol}: {e}")
    
    return results

"""Company IR RSS fetcher (whitelist-based)"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Company IR RSS whitelist (MVP: limited set)
COMPANY_IR_URLS = {
    "AMD": "https://ir.amd.com/news-events/press-releases?field_nir_news_date_value=&items_per_page=10",
    "INTC": "https://www.intc.com/news-events/press-releases",
    "NVDA": "https://nvidianews.nvidia.com/releases",
    "MSFT": "https://news.microsoft.com/source/topics/company/",
    "AAPL": "https://www.apple.com/newsroom/",
}

# Note: Many company IR pages don't have RSS, so this is limited
# For MVP, we'll try to fetch and handle failures gracefully

def fetch_company_ir(symbol: str, days: int = 3, user_agent: str = "news_service/1.0") -> List[Dict]:
    """Fetch company IR news for a symbol"""
    results = []
    
    ir_url = COMPANY_IR_URLS.get(symbol.upper())
    if not ir_url:
        logger.debug(f"No IR URL configured for {symbol}")
        return results
    
    try:
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/rss+xml"
        }
        
        response = requests.get(ir_url, headers=headers, timeout=30)
        
        # Try RSS first
        if 'rss' in response.headers.get('Content-Type', '').lower() or 'xml' in response.text[:100].lower():
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:10]:
                results.append({
                    "symbol": symbol.upper(),
                    "title": entry.get('title', '')[:500],
                    "url": entry.get('link', ''),
                    "source": "company_ir",
                    "evidence_type": "official",
                    "category": "company_news",
                    "published_at": None,
                    "origin_publisher": f"{symbol} IR",
                    "summary_text": entry.get('title', '')[:200]
                })
        else:
            logger.debug(f"IR page for {symbol} is HTML, not RSS - skipping for MVP")
        
        logger.info(f"Fetched {len(results)} IR items for {symbol}")
        
    except Exception as e:
        logger.error(f"Company IR fetch failed for {symbol}: {e}")
    
    return results

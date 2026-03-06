"""Bing News Search API fetcher (free tier)"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Note: Bing News API requires subscription key
# This is a fallback using RSS if API key not available
BING_NEWS_RSS = "https://www.bing.com/news/search?q={query}&format=rss"

def fetch_bing_news(symbol: str, days: int = 3, user_agent: str = "news_service/1.0") -> List[Dict]:
    """Fetch Bing News for a symbol"""
    results = []
    
    try:
        query = f"{symbol.upper()} stock news"
        url = BING_NEWS_RSS.format(query=query)
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/rss+xml"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.debug(f"Bing News returned {response.status_code} for {symbol}")
            return results
        
        # Parse RSS
        import feedparser
        feed = feedparser.parse(response.content)
        
        for entry in feed.entries[:15]:
            title = entry.get('title', '')
            link = entry.get('link', '')
            published = entry.get('published', '')
            source = entry.get('source', 'Bing News')
            
            pub_date = None
            if published:
                try:
                    pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                except:
                    pass
            
            if pub_date and pub_date < datetime.now() - timedelta(days=days):
                continue
            
            results.append({
                "symbol": symbol.upper(),
                "title": title[:500],
                "url": link,
                "source": "bing_news",
                "evidence_type": "media",
                "category": "company_news",
                "published_at": pub_date,
                "origin_publisher": str(source)[:100],
                "summary_text": title[:200]
            })
        
        logger.info(f"Fetched {len(results)} Bing News items for {symbol}")
        
    except Exception as e:
        logger.error(f"Bing News fetch failed for {symbol}: {e}")
    
    return results

"""Google News RSS fetcher"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

def fetch_google_news(symbol: str, days: int = 3, user_agent: str = "news_service/1.0") -> List[Dict]:
    """Fetch Google News for a symbol"""
    results = []
    
    try:
        query = quote(f"{symbol} stock OR {symbol} earnings OR {symbol} news")
        url = GOOGLE_NEWS_RSS.format(query=query)
        
        headers = {"User-Agent": user_agent, "Accept": "application/rss+xml"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        for entry in feed.entries[:15]:
            title = entry.get('title', '')
            link = entry.get('link', '')
            published = entry.get('published', '')
            
            # Extract publisher from source element (it's a dict with 'title' and 'href')
            source_obj = entry.get('source', {})
            publisher = source_obj.get('title', 'Unknown') if isinstance(source_obj, dict) else str(source_obj)[:100]
            
            pub_date = None
            if published:
                try:
                    pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                except:
                    try:
                        pub_date = datetime.strptime(published[:19], '%Y-%m-%d %H:%M:%S')
                    except:
                        pass
            
            if pub_date and pub_date < datetime.now() - timedelta(days=days):
                continue
            
            clean_title = title.rsplit(' - ', 1)[0] if ' - ' in title else title
            
            results.append({
                "symbol": symbol.upper(),
                "title": clean_title[:500],
                "url": link,
                "source": "google_news",
                "evidence_type": "media",
                "category": "company_news",
                "published_at": pub_date,
                "origin_publisher": publisher,
                "summary_text": clean_title[:200]
            })
        
        logger.info(f"Fetched {len(results)} Google News items for {symbol}")
        
    except Exception as e:
        logger.error(f"Google News fetch failed for {symbol}: {e}")
    
    return results

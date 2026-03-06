"""Seeking Alpha RSS fetcher"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Seeking Alpha RSS feeds (by stock symbol)
SA_RSS_URL = "https://seekingalpha.com/api/sa/symbol/{symbol}/articles"

def fetch_seeking_alpha(symbol: str, days: int = 3, user_agent: str = "news_service/1.0") -> List[Dict]:
    """Fetch Seeking Alpha articles for a symbol"""
    results = []
    
    try:
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json"
        }
        
        url = SA_RSS_URL.format(symbol=symbol.upper())
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.debug(f"Seeking Alpha returned {response.status_code} for {symbol}")
            return results
        
        data = response.json()
        articles = data.get("data", [])
        
        for article in articles[:15]:
            attributes = article.get("attributes", {})
            title = attributes.get("title", "")
            slug = attributes.get("slug", "")
            pub_date_str = attributes.get("publishOn", "")
            author = attributes.get("author", {}).get("nick", "")
            
            link = f"https://seekingalpha.com/article/{slug}" if slug else ""
            
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                except:
                    pass
            
            if pub_date and pub_date < datetime.now() - timedelta(days=days):
                continue
            
            summary = attributes.get("summary", "")[:200] if attributes.get("summary") else title[:200]
            
            results.append({
                "symbol": symbol.upper(),
                "title": title[:500],
                "url": link,
                "source": "seeking_alpha",
                "evidence_type": "media",
                "category": "analysis",
                "published_at": pub_date,
                "origin_publisher": f"Seeking Alpha - {author}" if author else "Seeking Alpha",
                "summary_text": summary
            })
        
        logger.info(f"Fetched {len(results)} Seeking Alpha items for {symbol}")
        
    except Exception as e:
        logger.error(f"Seeking Alpha fetch failed for {symbol}: {e}")
    
    return results

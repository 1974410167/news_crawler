"""Reddit Stock Market news fetcher"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Reddit API (public JSON endpoint)
REDDIT_STOCKS = [
    "https://www.reddit.com/r/stocks/search.json?q={symbol}&sort=new&limit=25",
    "https://www.reddit.com/r/investing/search.json?q={symbol}&sort=new&limit=25",
    "https://www.reddit.com/r/wallstreetbets/search.json?q={symbol}&sort=new&limit=25",
]

def fetch_reddit_stocks(symbol: str, days: int = 3, user_agent: str = "news_service/1.0") -> List[Dict]:
    """Fetch Reddit discussions for a symbol"""
    results = []
    
    try:
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json"
        }
        
        for reddit_url in REDDIT_STOCKS:
            url = reddit_url.format(symbol=symbol.upper())
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            
            if response.status_code != 200:
                continue
            
            data = response.json()
            posts = data.get("data", {}).get("children", [])
            
            for post in posts[:10]:
                post_data = post.get("data", {})
                title = post_data.get("title", "")
                permalink = post_data.get("permalink", "")
                created_utc = post_data.get("created_utc", 0)
                subreddit = post_data.get("subreddit", "")
                score = post_data.get("score", 0)
                
                # Filter low-quality posts
                if score < 5:
                    continue
                
                link = f"https://www.reddit.com{permalink}" if permalink else ""
                pub_date = datetime.fromtimestamp(created_utc) if created_utc else None
                
                if pub_date and pub_date < datetime.now() - timedelta(days=days):
                    continue
                
                selftext = post_data.get("selftext", "")[:200] if post_data.get("selftext") else ""
                
                results.append({
                    "symbol": symbol.upper(),
                    "title": f"[r/{subreddit}] {title[:400]}",
                    "url": link,
                    "source": "reddit",
                    "evidence_type": "social",
                    "category": "sentiment",
                    "published_at": pub_date,
                    "origin_publisher": f"Reddit r/{subreddit}",
                    "summary_text": selftext
                })
            
            # Only fetch first subreddit to avoid rate limiting
            break
        
        logger.info(f"Fetched {len(results)} Reddit items for {symbol}")
        
    except Exception as e:
        logger.error(f"Reddit fetch failed for {symbol}: {e}")
    
    return results

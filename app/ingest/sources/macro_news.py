"""宏观经济新闻爬虫"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 宏观新闻数据源
MACRO_SOURCES = {
    "reuters_business": {
        "url": "https://www.reuters.com/rss/business",
        "name": "Reuters Business",
        "category": "macro"
    },
    "bloomberg_economy": {
        "url": "https://www.bloomberg.com/feed/podcast/economics.xml",
        "name": "Bloomberg Economics",
        "category": "macro"
    },
    "cnbc_economy": {
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000115",
        "name": "CNBC Economy",
        "category": "macro"
    },
    "ft_economics": {
        "url": "https://www.ft.com/economics?format=rss",
        "name": "FT Economics",
        "category": "macro"
    },
    "investing_economic": {
        "url": "https://www.investing.com/rss/news.rss?category=economy",
        "name": "Investing.com Economy",
        "category": "macro"
    }
}

# 宏观关键词（用于过滤）
MACRO_KEYWORDS = [
    "Federal Reserve", "Fed", "interest rate", "inflation", "CPI", "PPI",
    "GDP", "unemployment", "economic", "central bank", "monetary policy",
    "fiscal policy", "treasury", "bond yield", "currency", "forex",
    "trade war", "tariff", "economic growth", "recession", "stimulus",
    "quantitative easing", "QE", "employment", "nonfarm", "jobs report",
    "consumer confidence", "PMI", "manufacturing", "retail sales",
    "housing data", "mortgage rate", "oil price", "commodity",
    "gold price", "dollar index", "emerging market", "global economy",
    "IMF", "World Bank", "ECB", "PBOC", "BOJ", "bank rate"
]

def fetch_macro_news(days: int = 3, user_agent: str = "news_service/1.0") -> List[Dict]:
    """抓取宏观经济新闻"""
    results = []
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/rss+xml, application/xml, text/html"
    }
    
    for source_key, source_info in MACRO_SOURCES.items():
        try:
            logger.info(f"Fetching macro news from {source_info['name']}...")
            
            response = requests.get(source_info["url"], headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"{source_info['name']} returned {response.status_code}")
                continue
            
            # 尝试解析 RSS
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:30]:
                title = entry.get('title', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                summary = entry.get('summary', '')[:500]
                publisher = entry.get('source', {}).get('title', source_info['name'])
                
                # 检查是否包含宏观关键词
                if not _is_macro_related(title, summary):
                    continue
                
                # 解析时间
                pub_date = None
                if published:
                    try:
                        pub_date = datetime.strptime(published[:19], '%Y-%m-%dT%H:%M')
                    except:
                        try:
                            pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                        except:
                            pass
                
                # 时间过滤
                if pub_date and pub_date < datetime.now() - timedelta(days=days):
                    continue
                
                results.append({
                    "symbol": "MACRO",  # 宏观新闻使用特殊标记
                    "title": title[:500],
                    "url": link,
                    "source": f"macro_{source_key}",
                    "evidence_type": "media",
                    "category": "macro",
                    "published_at": pub_date,
                    "origin_publisher": publisher,
                    "summary_text": summary[:300] if summary else title[:300]
                })
            
            logger.info(f"Fetched {len([r for r in results if r['source'] == f'macro_{source_key}'])} items from {source_info['name']}")
            
        except Exception as e:
            logger.error(f"Error fetching {source_info['name']}: {e}")
    
    logger.info(f"Total macro news fetched: {len(results)}")
    return results

def _is_macro_related(title: str, summary: str = "") -> bool:
    """检查内容是否与宏观经济相关"""
    text = f"{title} {summary}".lower()
    
    for keyword in MACRO_KEYWORDS:
        if keyword.lower() in text:
            return True
    
    return False

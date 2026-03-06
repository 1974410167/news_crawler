"""Longbridge 长桥资讯爬虫"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from bs4 import BeautifulSoup
import re
import random

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def get_random_ua():
    return random.choice(USER_AGENTS)

def fetch_longbridge_news(symbol: str, days: int = 3, user_agent: str = None) -> List[Dict]:
    """抓取长桥资讯"""
    results = []
    
    if user_agent is None:
        user_agent = get_random_ua()
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    }
    
    try:
        # 长桥英文新闻页面
        url = "https://www.longbridge.com/en/news"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"Longbridge returned {response.status_code}")
            return results
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有新闻链接
        news_links = soup.select('a[href*="/news/"]')
        
        symbol_upper = symbol.upper()
        symbol_lower = symbol.lower()
        
        for link in news_links:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # 过滤太短或无关的标题
            if not title or len(title) < 10:
                continue
            
            # 检查是否包含 symbol（大小写不敏感）
            if symbol_upper not in title.upper() and symbol_lower not in title.lower():
                continue
            
            # 构建完整 URL
            full_url = href if href.startswith('http') else f"https://www.longbridge.com{href}"
            
            # 尝试提取时间
            pub_date = None
            time_text = ""
            time_parent = link.find_parent()
            if time_parent:
                time_elem = time_parent.find(['time', 'span'], string=re.compile(r'\d+\s+(hour|day|min)s?\s+ago|ago'))
                if time_elem:
                    time_text = time_elem.get_text(strip=True)
                    pub_date = _parse_relative_time(time_text)
            
            # 时间过滤
            if pub_date and pub_date < datetime.now() - timedelta(days=days):
                continue
            
            results.append({
                "symbol": symbol_upper,
                "title": title[:500],
                "url": full_url,
                "source": "longbridge",
                "evidence_type": "media",
                "category": "company_news",
                "published_at": pub_date,
                "origin_publisher": "Longbridge",
                "summary_text": title[:200]
            })
        
        logger.info(f"Fetched {len(results)} Longbridge items for {symbol}")
        
    except Exception as e:
        logger.error(f"Longbridge fetch failed for {symbol}: {e}")
    
    return results

def _parse_relative_time(time_str: str) -> datetime:
    """解析相对时间（如 '4 hours ago', '1 day ago'）"""
    if not time_str:
        return None
    
    try:
        time_str = time_str.lower()
        
        if 'hour' in time_str:
            match = re.search(r'(\d+)', time_str)
            if match:
                hours = int(match.group(1))
                return datetime.now() - timedelta(hours=hours)
        
        if 'day' in time_str:
            match = re.search(r'(\d+)', time_str)
            if match:
                days = int(match.group(1))
                return datetime.now() - timedelta(days=days)
        
        if 'min' in time_str:
            match = re.search(r'(\d+)', time_str)
            if match:
                mins = int(match.group(1))
                return datetime.now() - timedelta(minutes=mins)
                
    except Exception as e:
        logger.debug(f"Error parsing time '{time_str}': {e}")
    
    return None

# Alias for backwards compatibility
fetch_longbridge = fetch_longbridge_news

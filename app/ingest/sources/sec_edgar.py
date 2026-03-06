"""SEC EDGAR RSS/API fetcher"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)

# SEC requires proper User-Agent with contact info
SEC_USER_AGENT = "news_service/1.0 (contact: 1909874106@qq.com)"

TIKER_CIK_CACHE = {
    "AMD": "0000002488", "AMZN": "0001018724", "ARM": "0001881994",
    "IBKR": "0001181198", "INTC": "0000050863", "META": "0001326801",
    "MSFT": "0000789019", "MSTR": "0001050446", "QCOM": "0000804328",
    "TSLA": "0001318605", "XIACY": None, "SPY": None, "SGOV": None,
    "AAPL": "0000320193", "GOOGL": "0001652044", "NVDA": "0001045810",
}

def get_cik(symbol: str) -> Optional[str]:
    return TIKER_CIK_CACHE.get(symbol.upper())

def fetch_sec_filings(symbol: str, days: int = 3, user_agent: str = SEC_USER_AGENT) -> List[Dict]:
    """Fetch SEC filings for a symbol"""
    results = []
    cik = get_cik(symbol)
    
    if not cik:
        logger.debug(f"No CIK mapping for {symbol}, skipping SEC fetch")
        return results
    
    try:
        headers = {"User-Agent": user_agent, "Accept": "application/atom+xml"}
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=include&start=0&count=40&output=atom"
        
        # SEC rate limiting: add delay before request
        time.sleep(1)
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 403:
            logger.warning(f"SEC EDGAR 403 for {symbol}, waiting 10s and retrying...")
            time.sleep(10)
            response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 403:
            logger.error(f"SEC EDGAR still 403 for {symbol} after retry")
            return results
        
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        for entry in feed.entries[:20]:
            title = entry.get('title', '')
            link = entry.get('link', '')
            published = entry.get('published', '')
            
            pub_date = None
            if published:
                try:
                    pub_date = datetime.strptime(published[:19], '%Y-%m-%dT%H:%M')
                except:
                    pass
            
            if pub_date and pub_date < datetime.now() - timedelta(days=days):
                continue
            
            category = "filing"
            if "8-K" in title: category = "filing"
            elif "10-K" in title or "10-Q" in title: category = "earnings"
            elif "4" in title: category = "insider"
            
            form_type = "Unknown"
            for ft in ["8-K", "10-K", "10-Q", "4", "SC 13G", "S-4", "DEF 14A"]:
                if ft in title:
                    form_type = ft
                    break
            
            results.append({
                "symbol": symbol.upper(), "title": title[:500], "url": link,
                "source": "sec_edgar", "evidence_type": "official",
                "category": category, "published_at": pub_date,
                "origin_publisher": "SEC EDGAR", "summary_text": f"SEC Filing: {form_type}"
            })
        
        logger.info(f"Fetched {len(results)} SEC filings for {symbol}")
        
    except Exception as e:
        logger.error(f"SEC EDGAR fetch failed for {symbol}: {e}")
    
    return results

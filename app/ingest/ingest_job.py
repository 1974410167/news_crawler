"""Main ingestion job with macro news support"""
import sys, os, re, hashlib, logging
from datetime import datetime, timedelta
from typing import List, Dict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .sources.sec_edgar import fetch_sec_filings
from .sources.google_news_rss import fetch_google_news
from .sources.yahoo_finance import fetch_yahoo_news
from .sources.seeking_alpha import fetch_seeking_alpha
from .sources.longbridge import fetch_longbridge_news
from .sources.macro_news import fetch_macro_news
from .dedup import generate_dedup_key
from ..db import SessionLocal, init_db
from ..models import NewsItem
from ..config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_FETCHERS = {
    "sec_edgar": fetch_sec_filings,
    "google_news": fetch_google_news,
    "yahoo_finance": fetch_yahoo_news,
    "seeking_alpha": fetch_seeking_alpha,
    "longbridge": fetch_longbridge_news,
}

DEFAULT_SOURCES = ["sec_edgar", "google_news", "yahoo_finance", "longbridge"]
DEFAULT_SYMBOLS = ["AMD", "AMZN", "ARM", "IBKR", "INTC", "META", "MSFT", "MSTR", "QCOM", "TSLA"]

def normalize_title(title):
    if not title: return ""
    return re.sub(r'[^\w\s]', '', re.sub(r'\s+', ' ', title.lower().strip()))

def is_dup(item, existing, hours=72):
    if existing.url == item["url"]: return True
    if existing.source != item["source"]: return False
    if hashlib.md5(normalize_title(existing.title).encode()).hexdigest() == hashlib.md5(normalize_title(item["title"]).encode()):
        if item.get("published_at") and existing.published_at:
            return abs((item["published_at"] - existing.published_at).total_seconds()) < hours * 3600
        return True
    return False

def run_ingestion(symbols=None, days=3, sources=None, include_macro=True):
    if symbols is None: symbols = DEFAULT_SYMBOLS
    if sources is None: sources = DEFAULT_SOURCES
    
    stats = {
        "fetched_total": 0, 
        "inserted_total": 0, 
        "dedup_skipped": 0, 
        "errors_by_source": {}, 
        "items_by_symbol": {},
        "macro_fetched": 0,
        "macro_inserted": 0
    }
    
    db = SessionLocal()
    try:
        init_db()
        
        # 1. 抓取股票相关新闻
        for symbol in symbols:
            logger.info(f"Processing stock: {symbol}")
            sym = {"fetched": 0, "inserted": 0, "dedup": 0}
            existing = db.query(NewsItem).filter(
                NewsItem.symbol == symbol, 
                NewsItem.inserted_at >= datetime.now() - timedelta(days=days)
            ).all()
            
            for source in sources:
                fetcher = SOURCE_FETCHERS.get(source)
                if not fetcher: continue
                try:
                    items = fetcher(symbol, days, settings.USER_AGENT)
                    sym["fetched"] += len(items)
                    stats["fetched_total"] += len(items)
                    
                    for item in items:
                        if any(is_dup(item, e) for e in existing):
                            sym["dedup"] += 1; stats["dedup_skipped"] += 1; continue
                        dk = generate_dedup_key(item["source"], item["url"], item["title"], item["published_at"])
                        if db.query(NewsItem).filter(NewsItem.dedup_key == dk).first():
                            sym["dedup"] += 1; stats["dedup_skipped"] += 1; continue
                        ni = NewsItem(symbol=item["symbol"], title=item["title"], url=item["url"], source=item["source"], evidence_type=item["evidence_type"], category=item["category"], published_at=item["published_at"], origin_publisher=item["origin_publisher"], summary_text=item["summary_text"], dedup_key=dk)
                        db.add(ni); sym["inserted"] += 1; stats["inserted_total"] += 1; existing.append(ni)
                    db.commit()
                except Exception as e:
                    logger.error(f"Error {source}/{symbol}: {e}")
                    stats["errors_by_source"][source] = stats["errors_by_source"].get(source, 0) + 1
                    db.rollback()
            
            stats["items_by_symbol"][symbol] = sym
            logger.info(f"  {symbol}: +{sym['inserted']} ({sym['fetched']} fetched)")
        
        # 2. 抓取宏观新闻
        if include_macro:
            logger.info("Fetching macro news...")
            try:
                macro_items = fetch_macro_news(days, settings.USER_AGENT)
                stats["macro_fetched"] = len(macro_items)
                
                existing_macro = db.query(NewsItem).filter(
                    NewsItem.category == "macro",
                    NewsItem.inserted_at >= datetime.now() - timedelta(days=days)
                ).all()
                
                macro_inserted = 0
                for item in macro_items:
                    if any(is_dup(item, e) for e in existing_macro):
                        stats["dedup_skipped"] += 1
                        continue
                    
                    dk = generate_dedup_key(item["source"], item["url"], item["title"], item["published_at"])
                    if db.query(NewsItem).filter(NewsItem.dedup_key == dk).first():
                        stats["dedup_skipped"] += 1
                        continue
                    
                    ni = NewsItem(
                        symbol=item["symbol"], title=item["title"], url=item["url"],
                        source=item["source"], evidence_type=item["evidence_type"],
                        category=item["category"], published_at=item["published_at"],
                        origin_publisher=item["origin_publisher"],
                        summary_text=item["summary_text"], dedup_key=dk
                    )
                    db.add(ni)
                    macro_inserted += 1
                    stats["inserted_total"] += 1
                    existing_macro.append(ni)
                
                db.commit()
                stats["macro_inserted"] = macro_inserted
                logger.info(f"  MACRO: +{macro_inserted} ({len(macro_items)} fetched)")
                
            except Exception as e:
                logger.error(f"Error fetching macro news: {e}")
                stats["errors_by_source"]["macro"] = 1
                db.rollback()
        
        return stats
    except Exception as e:
        logger.error(f"Failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    s = run_ingestion()
    print(f"\n{'='*60}")
    print(f"📊 Stock News: {s['fetched_total']} fetched, {s['inserted_total'] - s['macro_inserted']} inserted")
    print(f"📈 Macro News: {s['macro_fetched']} fetched, {s['macro_inserted']} inserted")
    print(f"⏭️  Dedup: {s['dedup_skipped']}")
    print(f"❌ Errors: {s['errors_by_source']}")

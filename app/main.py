"""FastAPI main application"""
from fastapi import FastAPI, Depends, HTTPException, Header, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from .config import settings
from .db import get_db, init_db, check_db_health
from .models import NewsItem
from .schemas import (
    HealthResponse, NewsItemResponse, SearchRequest, 
    BatchSearchRequest, BatchSearchResponse, IngestRunResponse,
    StatsResponse, StatsSummary
)
from .ingest.ingest_job import run_ingestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="News Service API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or x_api_key != settings.NEWS_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

@app.get("/v1/health", response_model=HealthResponse)
async def health_check(api_key: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    db_status = check_db_health(db)
    return HealthResponse(status="ok" if db_status == "ok" else "degraded", db_status=db_status, timestamp=datetime.now())

@app.get("/v1/news/search", response_model=List[NewsItemResponse])
async def search_news(
    symbol: str = Query(...), 
    days: int = Query(3, ge=1, le=30), 
    limit: int = Query(20, ge=1, le=100), 
    source: Optional[str] = Query(None), 
    api_key: str = Depends(verify_api_key), 
    db: Session = Depends(get_db)
):
    """搜索个股新闻"""
    cutoff_date = datetime.now() - timedelta(days=days)
    query = db.query(NewsItem).filter(NewsItem.symbol == symbol.upper(), NewsItem.published_at >= cutoff_date)
    if source: 
        query = query.filter(NewsItem.source == source)
    return query.order_by(desc(NewsItem.published_at)).limit(limit).all()

@app.post("/v1/news/search/batch", response_model=BatchSearchResponse)
async def batch_search(request: BatchSearchRequest, api_key: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    """批量搜索多只股票新闻"""
    cutoff_date = datetime.now() - timedelta(days=request.days)
    results = {}
    for symbol in request.symbols:
        query = db.query(NewsItem).filter(NewsItem.symbol == symbol.upper(), NewsItem.published_at >= cutoff_date)
        if request.sources: 
            query = query.filter(NewsItem.source.in_(request.sources))
        results[symbol.upper()] = query.order_by(desc(NewsItem.published_at)).limit(request.limit_per_symbol).all()
    return BatchSearchResponse(results=results)

@app.post("/v1/ingest/run", response_model=IngestRunResponse)
async def run_ingest_api(
    symbols: List[str] = Body(["AMD", "INTC", "MSFT"]), 
    days: int = Body(3), 
    sources: Optional[List[str]] = Body(None),
    include_macro: bool = Body(True),
    api_key: str = Depends(verify_api_key)
):
    """手动触发新闻采集"""
    stats = run_ingestion(symbols, days, sources, include_macro)
    return IngestRunResponse(**stats)


# ============== Stats APIs ==============

@app.get("/v1/stats/summary", response_model=StatsResponse)
async def get_stats_summary(
    hours: int = Query(24, ge=1, le=168, description="统计最近 N 小时"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """获取新闻统计摘要"""
    cutoff = datetime.now() - timedelta(hours=hours)
    
    # 基础查询
    base_query = db.query(NewsItem).filter(NewsItem.inserted_at >= cutoff)
    
    # 总数
    total = base_query.count()
    
    # 按分类统计
    by_category = db.query(NewsItem.category, func.count(NewsItem.id)).filter(
        NewsItem.inserted_at >= cutoff
    ).group_by(NewsItem.category).all()
    by_category_dict = {cat or 'unknown': count for cat, count in by_category}
    
    # 按来源统计
    by_source = db.query(NewsItem.source, func.count(NewsItem.id)).filter(
        NewsItem.inserted_at >= cutoff
    ).group_by(NewsItem.source).all()
    by_source_dict = {src: count for src, count in by_source}
    
    # 按 Symbol 统计（排除宏观新闻）
    by_symbol = db.query(NewsItem.symbol, func.count(NewsItem.id)).filter(
        NewsItem.inserted_at >= cutoff,
        NewsItem.symbol != None,
        NewsItem.symbol != ''
    ).group_by(NewsItem.symbol).all()
    by_symbol_dict = {sym: count for sym, count in by_symbol}
    
    # 宏观新闻数量
    macro_count = base_query.filter(NewsItem.category == 'macro').count()
    
    # 总记录数
    all_time_total = db.query(NewsItem).count()
    
    return StatsResponse(
        status="ok",
        period={
            "start": cutoff.isoformat(),
            "end": datetime.now().isoformat(),
            "hours": hours
        },
        summary=StatsSummary(
            total=total,
            by_category=by_category_dict,
            by_source=by_source_dict,
            by_symbol=by_symbol_dict,
            macro_count=macro_count,
            period_start=cutoff,
            period_end=datetime.now()
        ),
        all_time_total=all_time_total
    )


@app.get("/v1/stats/macro", response_model=dict)
async def get_macro_stats(
    hours: int = Query(24, ge=1, le=168, description="统计最近 N 小时"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """获取宏观新闻专项统计"""
    cutoff = datetime.now() - timedelta(hours=hours)
    
    macro_items = db.query(NewsItem).filter(
        NewsItem.inserted_at >= cutoff,
        NewsItem.category == 'macro'
    ).order_by(desc(NewsItem.published_at)).limit(50).all()
    
    by_source = db.query(NewsItem.source, func.count(NewsItem.id)).filter(
        NewsItem.inserted_at >= cutoff,
        NewsItem.category == 'macro'
    ).group_by(NewsItem.source).all()
    
    return {
        "total": len(macro_items),
        "period_hours": hours,
        "by_source": {src: count for src, count in by_source},
        "latest": [
            {
                "title": item.title,
                "source": item.source,
                "published_at": item.published_at.isoformat() if item.published_at else None
            }
            for item in macro_items[:10]
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)

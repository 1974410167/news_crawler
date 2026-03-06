"""Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID

class NewsItemBase(BaseModel):
    symbol: str
    title: str
    url: str
    source: str
    evidence_type: str
    category: str
    published_at: Optional[datetime] = None
    origin_publisher: Optional[str] = None
    summary_text: Optional[str] = None

class NewsItemCreate(NewsItemBase):
    dedup_key: str

class NewsItemResponse(NewsItemBase):
    id: UUID
    dedup_key: str
    inserted_at: datetime
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str
    db_status: str
    timestamp: datetime

class SearchRequest(BaseModel):
    symbol: str
    days: int = 3
    limit: int = 20
    source: Optional[str] = None

class BatchSearchRequest(BaseModel):
    symbols: List[str]
    days: int = 3
    limit_per_symbol: int = 5
    sources: Optional[List[str]] = None

class BatchSearchResponse(BaseModel):
    results: dict

class IngestRunResponse(BaseModel):
    fetched_total: int
    inserted_total: int
    dedup_skipped: int
    errors_by_source: dict
    macro_fetched: Optional[int] = None
    macro_inserted: Optional[int] = None


# ============== Stats Schemas ==============

class StatsSummary(BaseModel):
    """统计摘要"""
    total: int
    by_category: Optional[Dict[str, int]] = None
    by_source: Optional[Dict[str, int]] = None
    by_symbol: Optional[Dict[str, int]] = None
    macro_count: Optional[int] = None
    period_start: datetime
    period_end: datetime


class StatsResponse(BaseModel):
    """统计响应"""
    status: str = "ok"
    period: dict
    summary: StatsSummary
    all_time_total: int

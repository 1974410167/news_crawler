"""SQLAlchemy models"""
from sqlalchemy import Column, String, Text, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .db import Base
import uuid

class NewsItem(Base):
    __tablename__ = "news_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    evidence_type = Column(String(20), nullable=False)  # official, media
    category = Column(String(50), nullable=False)  # filing, earnings, company_news, macro, unknown
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    origin_publisher = Column(String(200), nullable=True)
    summary_text = Column(Text, nullable=True)
    dedup_key = Column(String(64), unique=True, nullable=False, index=True)
    inserted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_symbol_published', 'symbol', 'published_at', postgresql_ops={'published_at': 'DESC'}),
    )

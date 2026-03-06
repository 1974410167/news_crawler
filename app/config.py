"""Configuration management"""
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    NEWS_API_KEY: str = "dev-api-key"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DATABASE_URL: str = "postgresql+psycopg2://newsuser:newspass@localhost:5432/newsdb"
    INGEST_SOURCES: str = "sec_edgar,google_news"
    DEFAULT_DAYS: int = 3
    USER_AGENT: str = "news_service/1.0 (contact: 1909874106@qq.com)"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars
    
    @property
    def sources_list(self) -> List[str]:
        return [s.strip() for s in self.INGEST_SOURCES.split(",")]

settings = Settings()

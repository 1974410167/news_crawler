"""Database connection and session management"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from .models import NewsItem
    Base.metadata.create_all(bind=engine)

def check_db_health(db):
    """Check database connection"""
    try:
        db.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        return f"error: {str(e)}"

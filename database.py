from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import Config
import logging
from typing import Generator

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    Config.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def cleanup_old_data():
    """Clean up old data based on retention policy"""
    from datetime import datetime, timedelta
    from models import FinancialNews, ScrapingLog
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.now() - timedelta(days=Config.DATA_RETENTION_DAYS)
        
        # Delete old news articles
        deleted_news = db.query(FinancialNews).filter(
            FinancialNews.published_date < cutoff_date
        ).delete()
        
        # Delete old scraping logs
        deleted_logs = db.query(ScrapingLog).filter(
            ScrapingLog.start_time < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted_news} old news articles and {deleted_logs} old logs")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

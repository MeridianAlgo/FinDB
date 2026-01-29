from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

class FinancialNews(Base):
    __tablename__ = "financial_news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    author = Column(String(200))
    published_date = Column(DateTime, nullable=False, index=True)
    scraped_date = Column(DateTime, default=func.now(), index=True)
    
    # Sentiment analysis fields
    sentiment_score = Column(Float)  # -1 to 1
    sentiment_label = Column(String(20))  # positive, negative, neutral
    
    # Financial entity extraction
    mentioned_stocks = Column(Text)  # JSON array of stock symbols
    mentioned_companies = Column(Text)  # JSON array of company names
    mentioned_persons = Column(Text)  # JSON array of person names
    
    # Content classification
    category = Column(String(100))
    subcategory = Column(String(100))
    tags = Column(Text)  # JSON array of tags
    
    # Metadata
    word_count = Column(Integer)
    read_time_minutes = Column(Integer)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_source_published', 'source', 'published_date'),
        Index('idx_sentiment', 'sentiment_label', 'sentiment_score'),
        Index('idx_scraped_date', 'scraped_date'),
        Index('idx_published_date', 'published_date'),
    )

class ScrapingLog(Base):
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    articles_found = Column(Integer, default=0)
    articles_saved = Column(Integer, default=0)
    errors = Column(Text)
    success = Column(Boolean, default=False)

class APIUsage(Base):
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=func.now(), index=True)
    response_time_ms = Column(Integer)
    status_code = Column(Integer)
    user_agent = Column(String(500))
    ip_address = Column(String(45))

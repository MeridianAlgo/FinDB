from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class FinancialNews(Base):
    __tablename__ = "financial_news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    author: Mapped[str | None] = mapped_column(String(200))
    published_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    scraped_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # Sentiment analysis fields
    sentiment_score: Mapped[float | None] = mapped_column(Float)  # -1 to 1
    sentiment_label: Mapped[str | None] = mapped_column(String(20))  # positive, negative, neutral

    # Financial entity extraction
    mentioned_stocks: Mapped[str | None] = mapped_column(Text)  # JSON array of stock symbols
    mentioned_companies: Mapped[str | None] = mapped_column(Text)  # JSON array of company names
    mentioned_persons: Mapped[str | None] = mapped_column(Text)  # JSON array of person names

    # Content classification
    category: Mapped[str | None] = mapped_column(String(100))
    subcategory: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[str | None] = mapped_column(Text)  # JSON array of tags

    # Metadata
    word_count: Mapped[int | None] = mapped_column(Integer)
    read_time_minutes: Mapped[int | None] = mapped_column(Integer)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of_id: Mapped[int | None] = mapped_column(Integer)

    # Indexes for performance
    __table_args__ = (
        Index("idx_source_published", "source", "published_date"),
        Index("idx_sentiment", "sentiment_label", "sentiment_score"),
        Index("idx_scraped_date", "scraped_date"),
        Index("idx_published_date", "published_date"),
    )


class ScrapingLog(Base):
    __tablename__ = "scraping_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    articles_found: Mapped[int] = mapped_column(Integer, default=0)
    articles_saved: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str | None] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, default=False)


class APIUsage(Base):
    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    status_code: Mapped[int | None] = mapped_column(Integer)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    ip_address: Mapped[str | None] = mapped_column(String(45))

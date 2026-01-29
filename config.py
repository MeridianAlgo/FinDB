import os
from datetime import datetime, timedelta
from typing import List, Dict

class Config:
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///financial_news.db")
    
    # API settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Scraping settings
    SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "24"))
    MAX_ARTICLES_PER_SOURCE = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "100"))
    
    # News sources configuration
    NEWS_SOURCES = {
        "reuters": {
            "rss_url": "https://www.reuters.com/rssFeed/worldNews",
            "base_url": "https://www.reuters.com",
            "selector": "div.story-content",
            "title_selector": "h1",
            "content_selector": "div.StandardArticleBody__p",
            "date_selector": "time"
        },
        "yahoo_finance": {
            "rss_url": "https://finance.yahoo.com/news/rssindex",
            "base_url": "https://finance.yahoo.com",
            "selector": "div.caas-body",
            "title_selector": "h1",
            "content_selector": "div.caas-body p",
            "date_selector": "time"
        },
        "marketwatch": {
            "rss_url": "https://www.marketwatch.com/rss/topstories",
            "base_url": "https://www.marketwatch.com",
            "selector": "div.article__body",
            "title_selector": "h1",
            "content_selector": "div.article__body p",
            "date_selector": "time"
        },
        "seeking_alpha": {
            "rss_url": "https://seekingalpha.com/market_currents.xml",
            "base_url": "https://seekingalpha.com",
            "selector": "div.paywall-content",
            "title_selector": "h1",
            "content_selector": "div.paywall-content p",
            "date_selector": "time"
        },
        "cnbc": {
            "rss_url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "base_url": "https://www.cnbc.com",
            "selector": "div.group",
            "title_selector": "h1",
            "content_selector": "div.group p",
            "date_selector": "time"
        }
    }
    
    # Machine-readable output formats
    OUTPUT_FORMATS = ["json", "csv", "xml", "parquet"]
    
    # Data retention settings
    DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "365"))
    
    # GitHub Actions settings
    GITHUB_REPO = os.getenv("GITHUB_REPO", "")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "financial_news.log")

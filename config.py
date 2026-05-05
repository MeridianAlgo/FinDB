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
        "google_finance": {
            "rss_url": "https://news.google.com/rss/search?q=finance+OR+stock+OR+market&hl=en-US&gl=US&ceid=US:en",
            "base_url": "https://news.google.com",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div.article-body p, div.caas-body p, article p",
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
        },
        "bbc_business": {
            "rss_url": "http://feeds.bbci.co.uk/news/business/rss.xml",
            "base_url": "https://www.bbc.com",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div[data-component='text-block']",
            "date_selector": "time"
        },
        "guardian_business": {
            "rss_url": "https://www.theguardian.com/uk/business/rss",
            "base_url": "https://www.theguardian.com",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div.article-body-commercial-selector p",
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

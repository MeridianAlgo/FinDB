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

    # Content quality gate. Articles that fail these checks are dropped rather
    # than stored, so that sentiment/entity analytics are never computed over
    # non-prose (see NewsScraper.is_usable_content).
    MIN_CONTENT_CHARS = int(os.getenv("MIN_CONTENT_CHARS", "150"))

    # News sources configuration
    #
    # NOTE: "google_finance" (a news.google.com RSS search) was removed. Google
    # News RSS links are opaque redirect stubs (/rss/articles/CBMi...) that
    # resolve to the publisher only via a JS-gated batchexecute RPC; from a
    # plain HTTP client every article page is an empty JS shell, so extraction
    # always failed and fell back to storing the raw RSS markup as "content".
    # The publishers it aggregated are covered directly below instead.
    NEWS_SOURCES = {
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
        },

        # Direct feeds covering the publishers previously reached (unusably)
        # through google_finance. Each was validated for RSS availability and
        # full-text extraction before being added.
        "cnbc_finance": {
            "rss_url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
            "base_url": "https://www.cnbc.com",
            "selector": "div.group",
            "title_selector": "h1",
            "content_selector": "div.group p",
            "date_selector": "time"
        },
        "cnbc_economy": {
            "rss_url": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
            "base_url": "https://www.cnbc.com",
            "selector": "div.group",
            "title_selector": "h1",
            "content_selector": "div.group p",
            "date_selector": "time"
        },
        "business_insider": {
            "rss_url": "https://markets.businessinsider.com/rss/news",
            "base_url": "https://markets.businessinsider.com",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div.news-content p, article p",
            "date_selector": "time"
        },
        # NOTE: benzinga.com was evaluated and rejected. Its feed serves rich
        # articles to requests but returns HTTP 403 to aiohttp regardless of
        # headers (Cloudflare fingerprints the TLS/HTTP2 stack), so it would
        # fail on every run.
        "marketbeat": {
            "rss_url": "https://www.marketbeat.com/feed/",
            "base_url": "https://www.marketbeat.com",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div.article-body p, article p",
            "date_selector": "time"
        },
        "fortune": {
            "rss_url": "https://fortune.com/feed/fortune-feeds/?id=3230629",
            "base_url": "https://fortune.com",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div.articleBody p, article p",
            "date_selector": "time"
        },
        "forbes_business": {
            "rss_url": "https://www.forbes.com/business/feed/",
            "base_url": "https://www.forbes.com",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div.article-body p, article p",
            "date_selector": "time"
        },
        "cbc_business": {
            "rss_url": "https://www.cbc.ca/webfeed/rss/rss-business",
            "base_url": "https://www.cbc.ca",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div.story p, article p",
            "date_selector": "time"
        },
        "nasdaq": {
            "rss_url": "https://www.nasdaq.com/feed/rssoutbound?category=Markets",
            "base_url": "https://www.nasdaq.com",
            "selector": "article",
            "title_selector": "h1",
            "content_selector": "div.body__content p, article p",
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

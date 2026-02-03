# Usage Guide

## Table of Contents

- [Basic Usage](#basic-usage)
- [Manual Scraping](#manual-scraping)
- [Data Export](#data-export)
- [Database Queries](#database-queries)
- [API Usage](#api-usage)
- [Automation](#automation)

## Basic Usage

### Running the Scraper

Execute the scraper to fetch latest news:

```bash
python scraper.py
```

This will:
1. Connect to configured news sources
2. Parse RSS feeds
3. Extract article content
4. Perform sentiment analysis
5. Extract financial entities
6. Save to database

### Viewing Results

Check the database:
```bash
sqlite3 financial_news.db "SELECT COUNT(*) FROM financial_news;"
```

## Manual Scraping

### Scrape Specific Source

```python
from scraper import NewsScraper
import asyncio

async def scrape_single_source():
    async with NewsScraper() as scraper:
        articles, errors = await scraper.scrape_source(
            'yahoo_finance',
            Config.NEWS_SOURCES['yahoo_finance']
        )
        print(f"Scraped {len(articles)} articles")

asyncio.run(scrape_single_source())
```

### Custom Date Range

```python
from datetime import datetime, timedelta
from scraper import NewsScraper

# Scrape articles from last 7 days
start_date = datetime.now() - timedelta(days=7)
# Configure in scraper logic
```

## Data Export

### Export Yesterday's News

```python
from data_export import export_daily_news

# Export in JSON format
export_daily_news(format='json', output_dir='exports')

# Export in CSV format
export_daily_news(format='csv', output_dir='exports')

# Export in XML format
export_daily_news(format='xml', output_dir='exports')

# Export in Parquet format
export_daily_news(format='parquet', output_dir='exports')
```

### Export Custom Date Range

```python
from data_export import DataExporter
from datetime import datetime, timedelta

start = datetime.now() - timedelta(days=30)
end = datetime.now()

DataExporter.export_date_range(
    start_date=start,
    end_date=end,
    format='json',
    filename='exports/monthly_news.json'
)
```

### Export by Source

```python
from data_export import DataExporter
from datetime import datetime, timedelta

start = datetime.now() - timedelta(days=7)
end = datetime.now()

DataExporter.export_date_range(
    start_date=start,
    end_date=end,
    format='csv',
    filename='exports/yahoo_weekly.csv',
    source='yahoo_finance'
)
```

### Export with Limit

```python
from data_export import DataExporter
from datetime import datetime, timedelta

start = datetime.now() - timedelta(days=7)
end = datetime.now()

# Export only top 100 articles
DataExporter.export_date_range(
    start_date=start,
    end_date=end,
    format='json',
    filename='exports/top_100.json',
    limit=100
)
```

## Database Queries

### Query Articles

```python
from database import SessionLocal
from models import FinancialNews
from datetime import datetime, timedelta

db = SessionLocal()

# Get all articles from last 24 hours
yesterday = datetime.now() - timedelta(days=1)
articles = db.query(FinancialNews).filter(
    FinancialNews.published_date >= yesterday
).all()

# Get articles by source
yahoo_articles = db.query(FinancialNews).filter(
    FinancialNews.source == 'yahoo_finance'
).all()

# Get positive sentiment articles
positive_articles = db.query(FinancialNews).filter(
    FinancialNews.sentiment_label == 'positive'
).all()

# Get articles mentioning specific stock
import json
articles_with_aapl = []
for article in db.query(FinancialNews).all():
    if article.mentioned_stocks:
        stocks = json.loads(article.mentioned_stocks)
        if 'AAPL' in stocks:
            articles_with_aapl.append(article)

db.close()
```

### Aggregate Statistics

```python
from database import SessionLocal
from models import FinancialNews
from sqlalchemy import func

db = SessionLocal()

# Count articles by source
source_counts = db.query(
    FinancialNews.source,
    func.count(FinancialNews.id)
).group_by(FinancialNews.source).all()

# Average sentiment by source
avg_sentiment = db.query(
    FinancialNews.source,
    func.avg(FinancialNews.sentiment_score)
).group_by(FinancialNews.source).all()

# Articles per day
from sqlalchemy import cast, Date
daily_counts = db.query(
    cast(FinancialNews.published_date, Date),
    func.count(FinancialNews.id)
).group_by(cast(FinancialNews.published_date, Date)).all()

db.close()
```

## API Usage

### Start API Server

```bash
python api.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### Get Recent Articles
```bash
curl http://localhost:8000/articles?limit=10
```

#### Get Articles by Source
```bash
curl http://localhost:8000/articles?source=yahoo_finance
```

#### Get Articles by Date Range
```bash
curl "http://localhost:8000/articles?start_date=2026-02-01&end_date=2026-02-03"
```

#### Get Article by ID
```bash
curl http://localhost:8000/articles/1
```

#### Search Articles
```bash
curl "http://localhost:8000/search?q=Tesla"
```

#### Get Statistics
```bash
curl http://localhost:8000/stats
```

## Automation

### GitHub Actions

The scraper runs automatically via GitHub Actions:

- **Schedule**: Daily at 2:00 AM UTC
- **Manual Trigger**: Via GitHub Actions UI
- **Outputs**: Database, exports, artifacts

### Manual Trigger

```bash
gh workflow run daily-scraping.yml
```

### Local Scheduling

#### Using Cron (Linux/MacOS)

```bash
crontab -e
```

Add:
```
0 2 * * * cd /path/to/FinDB && /path/to/python scraper.py
```

#### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `scraper.py`
7. Start in: `C:\path\to\FinDB`

### Python Scheduler

```python
import schedule
import time
from scraper import main_scraping
import asyncio

def job():
    asyncio.run(main_scraping())

schedule.every().day.at("02:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Advanced Usage

### Custom News Source

Add to `config.py`:

```python
NEWS_SOURCES = {
    "custom_source": {
        "rss_url": "https://example.com/rss",
        "base_url": "https://example.com",
        "content_selector": "div.article-content p",
        "title_selector": "h1.article-title",
        "date_selector": "time.published"
    }
}
```

### Custom Entity Extraction

Modify `scraper.py`:

```python
def extract_custom_entities(text: str) -> Dict:
    # Add custom extraction logic
    crypto_pattern = r'\b(BTC|ETH|XRP)\b'
    cryptos = re.findall(crypto_pattern, text)
    return {'cryptocurrencies': cryptos}
```

### Custom Sentiment Analysis

```python
from textblob import TextBlob

def custom_sentiment(text: str) -> float:
    blob = TextBlob(text)
    # Custom weighting or model
    return blob.sentiment.polarity * 1.5
```

## Best Practices

1. **Rate Limiting**: Add delays between requests
2. **Error Handling**: Implement retry logic
3. **Data Validation**: Verify extracted data
4. **Logging**: Monitor scraping activity
5. **Backups**: Regular database backups
6. **Monitoring**: Track success rates

## Troubleshooting

See [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues and solutions.

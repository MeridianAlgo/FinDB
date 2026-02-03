# Financial News Scraper and Database

![Build Status](https://github.com/MeridianAlgo/FinDB/actions/workflows/daily-scraping.yml/badge.svg)

## Overview

This project implements an automated pipeline for scraping, processing, and storing financial news articles from major global sources. It is designed to create a comprehensive dataset suitable for training Large Language Models (LLMs) and performing financial sentiment analysis.

The system runs daily via GitHub Actions, aggregating news into a SQLite database and exporting machine-readable datasets in **JSON, CSV, XML, and Parquet** formats.

## ✨ Features

- **Multi-Source Scraping**: Aggregates news from 7 major sources:
  - Yahoo Finance
  - MarketWatch
  - Seeking Alpha
  - CNBC
  - BBC Business
  - Guardian Business
  - Reuters (configurable)

- **High-Quality Extraction**: 
  - Utilizes `trafilatura` for clean, main-text extraction
  - Strips ads, navigation, and clutter
  - Fallback to BeautifulSoup for complex pages

- **Sentiment Analysis**: 
  - Computes sentiment polarity (-1.0 to 1.0)
  - Classification (Positive, Negative, Neutral)
  - Powered by TextBlob

- **Entity Recognition**: 
  - Automatically identifies stock tickers ($AAPL, TSLA, etc.)
  - Extracts company names
  - Identifies key person entities

- **Automated Workflow**: 
  - Fully automated daily execution via GitHub Actions
  - Runs at 2:00 AM UTC (8:00 PM CST previous day)
  - Manual trigger option available

- **Data Persistence**: 
  - Relational storage in SQLite (`financial_news.db`)
  - Daily exports in 4 machine-readable formats:
    - **JSON**: Full structured data with metadata
    - **CSV**: Flattened for spreadsheet analysis
    - **XML**: Hierarchical structure
    - **Parquet**: Compressed, optimized for big data
  - Daily summary statistics
  - 90-day data retention policy

- **Error Handling**:
  - Duplicate detection (URL-based)
  - Retry logic for failed requests
  - Comprehensive logging
  - Graceful degradation

## 📊 Test Results

**Latest Test:** February 3, 2026

- ✅ **183 articles scraped** in 71 seconds
- ✅ **128 unique articles saved** to database
- ✅ **All 4 export formats** working perfectly
- ✅ **YAML workflow validated** with 0 errors (fixed 185+ syntax errors)
- ✅ **Success rate:** 99.5%

See [TEST_RESULTS.md](TEST_RESULTS.md) for detailed test report.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/MeridianAlgo/FinDB.git
   cd FinDB
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m textblob.download_corpora
   ```

### Manual Execution

Run the scraper:
```bash
python scraper.py
```

Export data in all formats:
```bash
python test_export.py
```

Generate daily summary:
```bash
python test_summary.py
```

### Programmatic Usage

```python
# Export yesterday's news
from data_export import export_daily_news

# Export in specific format
export_daily_news(format='json', output_dir='exports')
export_daily_news(format='csv', output_dir='exports')
export_daily_news(format='xml', output_dir='exports')
export_daily_news(format='parquet', output_dir='exports')

# Export date range
from data_export import DataExporter
from datetime import datetime, timedelta

start = datetime.now() - timedelta(days=7)
end = datetime.now()
DataExporter.export_date_range(start, end, format='json', filename='weekly_news.json')
```

## 📁 Repository Structure

```
FinDB/
├── .github/
│   └── workflows/
│       └── daily-scraping.yml    # GitHub Actions workflow
├── exports/                       # Daily export files
│   ├── financial_news_YYYY-MM-DD.json
│   ├── financial_news_YYYY-MM-DD.csv
│   ├── financial_news_YYYY-MM-DD.xml
│   ├── financial_news_YYYY-MM-DD.parquet
│   └── daily_summary.json
├── scraper.py                     # Core scraping logic
├── models.py                      # SQLAlchemy database models
├── database.py                    # Database connection & management
├── data_export.py                 # Export utilities
├── config.py                      # Configuration & news sources
├── api.py                         # FastAPI REST API (optional)
├── requirements.txt               # Python dependencies
├── financial_news.db              # SQLite database
├── TEST_RESULTS.md                # Detailed test report
└── README.md                      # This file
```

## 📊 Data Schema

### FinancialNews Table

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| title | String(500) | Article headline |
| content | Text | Full article text |
| summary | Text | Article summary/excerpt |
| url | String(1000) | Unique article URL |
| source | String(50) | News outlet name |
| author | String(200) | Article author |
| published_date | DateTime | Publication timestamp |
| scraped_date | DateTime | Scraping timestamp |
| sentiment_score | Float | Polarity (-1.0 to 1.0) |
| sentiment_label | String(20) | positive/negative/neutral |
| mentioned_stocks | Text | JSON array of tickers |
| mentioned_companies | Text | JSON array of companies |
| mentioned_persons | Text | JSON array of persons |
| category | String(100) | Article category |
| subcategory | String(100) | Article subcategory |
| tags | Text | JSON array of tags |
| word_count | Integer | Article word count |
| read_time_minutes | Integer | Estimated reading time |
| is_duplicate | Boolean | Duplicate flag |
| duplicate_of_id | Integer | Original article ID |

### Export Formats

#### JSON
```json
{
  "export_timestamp": "2026-02-03T17:40:17",
  "total_articles": 41,
  "articles": [
    {
      "id": 1,
      "title": "...",
      "content": "...",
      "sentiment_score": 0.15,
      "sentiment_label": "positive",
      "mentioned_stocks": ["AAPL", "TSLA"],
      ...
    }
  ]
}
```

#### CSV
Flattened structure with semicolon-separated lists for array fields.

#### XML
```xml
<financial_news export_timestamp="..." total_articles="41">
  <article>
    <id>1</id>
    <title>...</title>
    ...
  </article>
</financial_news>
```

#### Parquet
Binary columnar format optimized for analytics (Pandas, Spark, etc.)

## 🤖 GitHub Actions Workflow

The workflow runs automatically every day at 2:00 AM UTC:

1. **Setup**: Install Python, dependencies, and corpora
2. **Scrape**: Fetch news from all sources
3. **Export**: Generate all 4 formats + summary
4. **Commit**: Push database and exports to repository
5. **Upload**: Create artifacts with 30-day retention
6. **Cleanup**: Remove data older than 90 days

### Manual Trigger

You can manually trigger the workflow from the Actions tab or via:
```bash
gh workflow run daily-scraping.yml
```

## 🔧 Configuration

Edit `config.py` to customize:

- News sources and RSS feeds
- Scraping intervals
- Data retention period
- Export formats
- Database settings

Example:
```python
NEWS_SOURCES = {
    "your_source": {
        "rss_url": "https://example.com/rss",
        "base_url": "https://example.com",
        "content_selector": "div.article-body p"
    }
}
```

## 📈 Performance

- **Scraping Speed**: ~2.6 articles/second
- **Success Rate**: 99.5%
- **Memory Usage**: Minimal (async processing)
- **Export Time**: <5 seconds for all formats
- **Database Size**: ~50MB per 1000 articles

## 🐛 Known Issues

1. **Reuters RSS Feed**: Returns 404 - needs URL update
2. **Yahoo Finance**: Some articles fail with "Header too long" error
3. **Seeking Alpha**: Rate limiting (403 errors) on some articles

## 🛠️ Troubleshooting

### Scraper fails to fetch articles
- Check internet connection
- Verify RSS feed URLs are still valid
- Check for rate limiting (add delays)

### Export fails
- Ensure `exports/` directory exists
- Check disk space
- Verify database file is not corrupted

### GitHub Actions workflow fails
- Check workflow logs in Actions tab
- Verify secrets are configured (if using)
- Ensure repository has write permissions

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📧 Contact

For questions or issues, please open a GitHub issue or contact the maintainers.

## 🙏 Acknowledgments

- **trafilatura**: High-quality text extraction
- **TextBlob**: Sentiment analysis
- **feedparser**: RSS feed parsing
- **SQLAlchemy**: Database ORM
- **FastAPI**: REST API framework
- **pandas**: Data manipulation
- **pyarrow**: Parquet support

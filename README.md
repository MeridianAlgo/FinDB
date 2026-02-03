# Financial News Scraper and Database

[![Build Status](https://github.com/MeridianAlgo/FinDB/actions/workflows/daily-scraping.yml/badge.svg)](https://github.com/MeridianAlgo/FinDB/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Database](https://img.shields.io/badge/database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![API](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

## Overview

An automated pipeline for scraping, processing, and storing financial news articles from major global sources. Designed for creating comprehensive datasets suitable for training Large Language Models (LLMs), performing financial sentiment analysis, and conducting market research.

The system executes daily via GitHub Actions, aggregating news into a SQLite database and exporting machine-readable datasets in JSON, CSV, XML, and Parquet formats.

## Key Features

### Multi-Source Aggregation
Collects news from 7 major financial sources:
- Yahoo Finance
- MarketWatch
- Seeking Alpha
- CNBC
- BBC Business
- Guardian Business
- Reuters

### Intelligent Content Extraction
- High-quality text extraction using trafilatura
- Automatic removal of advertisements and navigation elements
- Fallback parsing with BeautifulSoup for complex pages
- Metadata extraction (author, publish date, tags)

### Advanced Analytics
- Sentiment analysis with polarity scoring (-1.0 to 1.0)
- Automatic classification (positive, negative, neutral)
- Financial entity extraction (stock tickers, companies, persons)
- Word count and reading time estimation

### Automated Workflow
- Daily scheduled execution at 2:00 AM UTC
- Manual trigger capability via GitHub Actions
- Automatic data export in multiple formats
- Git-based version control for all data
- 30-day artifact retention
- 90-day data retention policy

### Multiple Export Formats
- **JSON**: Full structured data with nested objects
- **CSV**: Flattened format for spreadsheet analysis
- **XML**: Hierarchical structure for XML parsers
- **Parquet**: Compressed columnar format for big data analytics

### RESTful API
- Query articles by date, source, sentiment
- Full-text search capabilities
- Aggregated statistics and trends
- Export functionality via API
- Pagination and filtering support

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/MeridianAlgo/FinDB.git
cd FinDB

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required corpora
python -m textblob.download_corpora
```

### Basic Usage

```bash
# Run scraper
python scraper.py

# Export data
python -c "from data_export import export_daily_news; export_daily_news('json', 'exports')"

# Start API server
python api.py
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions
- [Usage Guide](docs/USAGE.md) - Examples and best practices
- [API Documentation](docs/API.md) - Complete API reference
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Test Results](docs/TEST_RESULTS.md) - Latest test reports

## Project Structure

```
FinDB/
├── .github/
│   └── workflows/
│       └── daily-scraping.yml    # Automated workflow
├── docs/                          # Documentation
│   ├── INSTALLATION.md
│   ├── USAGE.md
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── TEST_RESULTS.md
├── exports/                       # Daily export files
├── scripts/                       # Utility scripts
├── tests/                         # Test suite
├── scraper.py                     # Core scraping logic
├── models.py                      # Database models
├── database.py                    # Database management
├── data_export.py                 # Export utilities
├── config.py                      # Configuration
├── api.py                         # REST API
├── requirements.txt               # Dependencies
├── financial_news.db              # SQLite database
└── README.md                      # This file
```

## Database Schema

### FinancialNews Table

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| title | String(500) | Article headline |
| content | Text | Full article text |
| summary | Text | Article summary |
| url | String(1000) | Unique article URL |
| source | String(50) | News outlet identifier |
| author | String(200) | Article author |
| published_date | DateTime | Publication timestamp |
| scraped_date | DateTime | Scraping timestamp |
| sentiment_score | Float | Polarity score (-1.0 to 1.0) |
| sentiment_label | String(20) | Sentiment classification |
| mentioned_stocks | Text | JSON array of stock tickers |
| mentioned_companies | Text | JSON array of company names |
| mentioned_persons | Text | JSON array of person names |
| category | String(100) | Article category |
| subcategory | String(100) | Article subcategory |
| tags | Text | JSON array of tags |
| word_count | Integer | Article word count |
| read_time_minutes | Integer | Estimated reading time |
| is_duplicate | Boolean | Duplicate detection flag |
| duplicate_of_id | Integer | Reference to original article |

## Performance Metrics

- **Scraping Speed**: 2.6 articles/second
- **Success Rate**: 99.5%
- **Memory Usage**: Minimal (async processing)
- **Export Time**: <5 seconds for all formats
- **Database Size**: ~50MB per 1000 articles

## Technology Stack

### Core Technologies
- Python 3.11+
- SQLite 3
- SQLAlchemy 2.0

### Scraping & Processing
- aiohttp 3.9 - Async HTTP client
- feedparser 6.0 - RSS/Atom parsing
- trafilatura 1.6 - Content extraction
- BeautifulSoup4 4.12 - HTML parsing
- TextBlob 0.17 - Sentiment analysis

### API & Data Export
- FastAPI 0.104 - Web framework
- Uvicorn 0.24 - ASGI server
- pandas 2.1 - Data manipulation
- pyarrow 14.0 - Parquet support

### Automation
- GitHub Actions - CI/CD platform
- schedule 1.2 - Task scheduling

## Configuration

Edit `config.py` to customize:

```python
# Scraping settings
SCRAPE_INTERVAL_HOURS = 24
MAX_ARTICLES_PER_SOURCE = 100

# Data retention
DATA_RETENTION_DAYS = 365

# Export formats
OUTPUT_FORMATS = ["json", "csv", "xml", "parquet"]

# News sources
NEWS_SOURCES = {
    "source_name": {
        "rss_url": "https://example.com/rss",
        "base_url": "https://example.com",
        "content_selector": "div.article-body p"
    }
}
```

## API Endpoints

```bash
# Get recent articles
GET /articles?limit=10&source=yahoo_finance

# Search articles
GET /search?q=Tesla

# Get statistics
GET /stats

# Export data
GET /export?format=csv&start_date=2026-02-01
```

See [API Documentation](docs/API.md) for complete reference.

## Automation

### GitHub Actions Workflow

The scraper runs automatically:
- **Schedule**: Daily at 2:00 AM UTC
- **Manual Trigger**: Via GitHub Actions UI
- **Outputs**: Database, exports, artifacts

### Manual Trigger

```bash
gh workflow run daily-scraping.yml
```

## Testing

Latest test results (February 3, 2026):
- 183 articles scraped in 71 seconds
- 128 unique articles saved
- All 4 export formats validated
- 99.5% success rate

See [Test Results](docs/TEST_RESULTS.md) for detailed report.

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:
- Open a [GitHub Issue](https://github.com/MeridianAlgo/FinDB/issues)
- Review [Documentation](docs/)
- Contact maintainers

## Acknowledgments

Built with:
- [trafilatura](https://github.com/adbar/trafilatura) - Content extraction
- [TextBlob](https://textblob.readthedocs.io/) - Sentiment analysis
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [pandas](https://pandas.pydata.org/) - Data manipulation

## Citation

If you use this project in your research, please cite:

```bibtex
@software{findb2026,
  title = {Financial News Scraper and Database},
  author = {MeridianAlgo},
  year = {2026},
  url = {https://github.com/MeridianAlgo/FinDB}
}
```

## Roadmap

### Planned Features
- Real-time scraping with WebSockets
- Advanced ML models for entity extraction
- Multi-language support
- Cryptocurrency news sources
- Social media integration
- Data visualization dashboard

### Technical Improvements
- Migration to PostgreSQL
- Caching layer implementation
- GraphQL API
- Full-text search
- Comprehensive test suite
- Performance optimization

## Status

**Current Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: February 3, 2026

---

**Maintained by**: [MeridianAlgo](https://github.com/MeridianAlgo)  
**Repository**: [github.com/MeridianAlgo/FinDB](https://github.com/MeridianAlgo/FinDB)

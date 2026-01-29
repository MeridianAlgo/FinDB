# Financial News Scraper (FinDB)

A comprehensive financial news scraping system that automatically collects financial news from multiple sources and provides machine-readable data exports and API access.

## Features

- **Automated Daily Scraping**: Scrapes financial news from multiple sources every night
- **Machine-Readable Formats**: Exports data in JSON, CSV, XML, and Parquet formats
- **REST API**: Full API for accessing news data with filtering and search
- **GitHub Actions**: Automated daily workflow with data commits
- **Database Storage**: SQLite database with structured news data
- **Financial Entity Extraction**: Automatically extracts stocks, companies, and persons mentioned

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/MeridianAlgo/FinDB.git
cd FinDB

# Install dependencies
pip install -r requirements.txt
```

### Test the Scraper

```bash
# Run the simple test scraper
python test_scraper.py

# Run the full scraper (may encounter anti-bot measures)
python scraper.py
```

### Start the API Server

```bash
# Start the FastAPI server
python api.py

# Or use uvicorn directly
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

## API Endpoints

- `GET /` - API information
- `GET /api/articles` - Get articles with filtering
- `GET /api/articles/{id}` - Get specific article
- `POST /api/search` - Search articles
- `GET /api/export/yesterday` - Export yesterday's news
- `POST /api/export` - Custom export with filters
- `GET /api/stats` - Database statistics
- `GET /api/sources` - Available news sources

## Data Sources

Currently configured to scrape from:
- Yahoo Finance
- MarketWatch
- Seeking Alpha
- CNBC
- Reuters

## Automated Workflow

The system includes a GitHub Actions workflow that:
1. Runs daily at 2:00 AM UTC
2. Scrapes news from all sources
3. Exports data in all formats
4. Commits results back to the repository
5. Creates GitHub releases (manual trigger)

## Project Structure

```
FinDB/
├── api.py              # FastAPI REST API
├── scraper.py          # Main news scraper
├── test_scraper.py     # Simple test scraper
├── config.py           # Configuration settings
├── models.py           # Database models
├── database.py         # Database operations
├── data_export.py      # Data export utilities
├── requirements.txt    # Python dependencies
├── .github/workflows/  # GitHub Actions
└── README.md          # This file
```

## Notes

- Some news sources have anti-bot measures that may block scraping
- The test scraper (`test_scraper.py`) is more reliable for basic RSS feeds
- GitHub Actions workflow may need adjustments for production use
- Database file (`financial_news.db`) is included in the repository

## License

This project is open source and available under the MIT License.

# Financial News Scraper and Database

![Build Status](https://github.com/MeridianAlgo/FinDB/actions/workflows/daily-scraping.yml/badge.svg)

## Overview

This project implements an automated pipeline for scraping, processing, and storing financial news articles from major global sources. It is designed to create a comprehensive dataset suitable for training Large Language Models (LLMs) and performing financial sentiment analysis.

The system runs daily via GitHub Actions, aggregating news into a SQLite database and exporting machine-readable datasets in JSON, CSV, XML, and Parquet formats.

## Features

- **Multi-Source Scraping**: Aggregates news from Reuters, Yahoo Finance, MarketWatch, Seeking Alpha, CNBC, BBC Business, and Guardian Business.
- **High-Quality Extraction**: Utilizes `trafilatura` for clean, main-text extraction, stripping ads and clutter.
- **Sentiment Analysis**: Computes sentiment polarity and classification (Positive, Negative, Neutral) for each article.
- **Entity Recognition**: Automatically identifies and extracts stock tickers, company names, and key person entities.
- **Automated Workflow**: Fully automated daily execution via GitHub Actions.
- **Data Persistence**: 
  - Relational storage in SQLite (`financial_news.db`).
  - Daily exports in `exports/` directory supporting JSON, CSV, XML, and Parquet.

## Repository Structure

- `scraper.py`: Core logic for fetching feeds, extracting content, and processing metadata.
- `models.py`: SQLAlchemy database definitions for articles and logs.
- `database.py`: Database connection handling and session management.
- `data_export.py`: Utilities for converting database records into flat files.
- `config.py`: Configuration for sources, URLs, and extraction rules.
- `.github/workflows/daily-scraping.yml`: CI/CD configuration for daily automation.

## Setup and Usage

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/MeridianAlgo/FinDB.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m textblob.download_corpora
   ```

### Manual Execution

To run the scraper manually:

```bash
python scraper.py
```

To export data manually:

```python
from data_export import export_daily_news
export_daily_news(format='csv', output_dir='exports')
```

## Data Schema

Each article record contains the following fields:

- **Source**: Originating news outlet.
- **Title**: Article headline.
- **Content**: Full, cleaned article text.
- **Published Date**: ISO 8601 formatted timestamp.
- **Sentiment**: Polarity score (-1.0 to 1.0) and Label.
- **Entities**: JSON lists of Stock Tickers, Companies, and Persons.
- **Tags**: Source-provided categorization tags.
- **Read Metrics**: Word count and estimated reading time.

## License

[Add License Information Here]

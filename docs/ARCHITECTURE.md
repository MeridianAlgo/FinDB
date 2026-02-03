# System Architecture

## Overview

The Financial News Scraper is designed as a modular, scalable system for automated news aggregation, processing, and storage.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
│                  (Scheduled Workflow)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Scraper Module                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ RSS Parser   │  │   Content    │  │   Entity     │     │
│  │              │─▶│  Extractor   │─▶│  Extraction  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                            ▼                                │
│                  ┌──────────────────┐                       │
│                  │    Sentiment     │                       │
│                  │    Analysis      │                       │
│                  └──────────────────┘                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Database Layer                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              SQLite Database                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │ Financial  │  │  Scraping  │  │    API     │    │  │
│  │  │    News    │  │    Logs    │  │   Usage    │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Export Module                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   JSON   │  │   CSV    │  │   XML    │  │ Parquet  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
│                   (FastAPI)                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  REST Endpoints  │  Query Interface  │  Export API  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Scraper Module

**Purpose**: Fetch and process news articles from multiple sources

**Components**:

#### RSS Parser
- Fetches RSS feeds from configured sources
- Parses XML/RSS format
- Extracts basic metadata (title, URL, publish date)
- Handles feed-specific formats

#### Content Extractor
- Downloads full article HTML
- Uses trafilatura for main content extraction
- Falls back to BeautifulSoup for complex pages
- Cleans and normalizes text
- Extracts author and metadata

#### Entity Extraction
- Identifies stock tickers using regex patterns
- Extracts company names using NLP
- Identifies person names
- Stores entities as JSON arrays

#### Sentiment Analysis
- Uses TextBlob for sentiment scoring
- Calculates polarity (-1.0 to 1.0)
- Classifies as positive/negative/neutral
- Stores both score and label

**Technologies**:
- aiohttp: Async HTTP requests
- feedparser: RSS/Atom parsing
- trafilatura: Content extraction
- BeautifulSoup4: HTML parsing
- TextBlob: Sentiment analysis

### 2. Database Layer

**Purpose**: Persistent storage and data management

**Schema**:

#### FinancialNews Table
- Primary storage for articles
- Indexed on: URL, source, published_date, scraped_date
- Composite indexes for common queries
- UNIQUE constraint on URL for deduplication

#### ScrapingLog Table
- Tracks scraping sessions
- Records success/failure metrics
- Stores error messages
- Used for monitoring and debugging

#### APIUsage Table
- Logs API requests
- Tracks response times
- Monitors usage patterns
- Used for analytics

**Technologies**:
- SQLAlchemy: ORM and query builder
- SQLite: Database engine
- Alembic: Schema migrations

### 3. Export Module

**Purpose**: Convert database records to various formats

**Formats**:

#### JSON
- Full structured data
- Nested objects preserved
- Human-readable
- ~150KB per 100 articles

#### CSV
- Flattened structure
- Semicolon-separated lists
- Spreadsheet compatible
- ~45KB per 100 articles

#### XML
- Hierarchical structure
- Standard XML format
- Parser-friendly
- ~180KB per 100 articles

#### Parquet
- Columnar binary format
- Highly compressed
- Analytics optimized
- ~25KB per 100 articles

**Technologies**:
- pandas: Data manipulation
- pyarrow: Parquet support
- xml.etree: XML generation

### 4. API Layer

**Purpose**: Programmatic access to data

**Features**:
- RESTful endpoints
- Query filtering
- Pagination support
- Export functionality
- Statistics aggregation

**Technologies**:
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation

### 5. Automation Layer

**Purpose**: Scheduled execution and orchestration

**Components**:

#### GitHub Actions Workflow
- Scheduled daily runs
- Manual trigger support
- Artifact management
- Git integration

#### Jobs
1. **scrape-news**: Main scraping job
2. **cleanup**: Data retention management

**Technologies**:
- GitHub Actions: CI/CD platform
- Cron: Scheduling

## Data Flow

### Scraping Flow

```
1. Trigger (Schedule/Manual)
   ↓
2. Initialize Scraper
   ↓
3. For each source:
   a. Fetch RSS feed
   b. Parse entries
   c. For each entry:
      - Download article
      - Extract content
      - Analyze sentiment
      - Extract entities
      - Save to database
   ↓
4. Generate exports
   ↓
5. Commit to repository
   ↓
6. Upload artifacts
```

### Query Flow

```
1. API Request
   ↓
2. Validate parameters
   ↓
3. Build database query
   ↓
4. Execute query
   ↓
5. Transform results
   ↓
6. Return JSON response
```

### Export Flow

```
1. Export request
   ↓
2. Query database
   ↓
3. Transform to format
   ↓
4. Write to file
   ↓
5. Return file path
```

## Scalability Considerations

### Current Limitations
- Single SQLite database
- Synchronous exports
- No distributed processing
- Limited to GitHub Actions resources

### Scaling Strategies

#### Horizontal Scaling
- Migrate to PostgreSQL/MySQL
- Implement connection pooling
- Add read replicas
- Use message queues (RabbitMQ/Redis)

#### Vertical Scaling
- Increase GitHub Actions resources
- Optimize database queries
- Add caching layer (Redis)
- Implement batch processing

#### Performance Optimization
- Add database indexes
- Implement query caching
- Use async I/O throughout
- Optimize entity extraction

## Security Considerations

### Current Implementation
- No authentication required
- Public repository
- No sensitive data storage
- Rate limiting not enforced

### Production Recommendations
- Implement API key authentication
- Add rate limiting
- Use environment variables for secrets
- Enable HTTPS only
- Implement input validation
- Add SQL injection protection
- Use prepared statements

## Monitoring and Logging

### Current Logging
- Python logging module
- INFO level by default
- Console output
- Scraping logs in database

### Recommended Monitoring
- Application performance monitoring (APM)
- Error tracking (Sentry)
- Uptime monitoring
- Database performance metrics
- API response times

## Deployment Options

### Current: GitHub Actions
- Pros: Free, automated, version controlled
- Cons: Limited resources, public logs

### Alternative: Cloud Deployment

#### AWS
- EC2: Virtual machines
- Lambda: Serverless functions
- RDS: Managed database
- S3: File storage

#### Google Cloud
- Compute Engine: VMs
- Cloud Functions: Serverless
- Cloud SQL: Database
- Cloud Storage: Files

#### Azure
- Virtual Machines
- Functions: Serverless
- SQL Database
- Blob Storage

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "scraper.py"]
```

## Technology Stack

### Core
- Python 3.11+
- SQLite 3
- SQLAlchemy 2.0

### Scraping
- aiohttp 3.9
- feedparser 6.0
- trafilatura 1.6
- BeautifulSoup4 4.12

### Analysis
- TextBlob 0.17
- NLTK 3.9

### API
- FastAPI 0.104
- Uvicorn 0.24
- Pydantic 2.5

### Data Processing
- pandas 2.1
- pyarrow 14.0

### Automation
- GitHub Actions
- schedule 1.2

## Future Enhancements

### Planned Features
1. Real-time scraping with WebSockets
2. Machine learning for entity extraction
3. Advanced sentiment models (BERT, FinBERT)
4. Multi-language support
5. Image extraction and analysis
6. Video transcript processing
7. Social media integration
8. Cryptocurrency news sources

### Technical Improvements
1. Migrate to PostgreSQL
2. Implement caching layer
3. Add GraphQL API
4. Implement full-text search
5. Add data visualization dashboard
6. Implement A/B testing
7. Add comprehensive test suite
8. Implement CI/CD pipeline

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for architecture guidelines and contribution process.

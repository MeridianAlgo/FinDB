# API Documentation

## Overview

The Financial News Scraper provides a RESTful API built with FastAPI for accessing scraped news data programmatically.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. For production deployments, implement API key authentication.

## Endpoints

### Health Check

Check API status and version.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

### Get Articles

Retrieve articles with optional filtering.

**Endpoint**: `GET /articles`

**Query Parameters**:
- `limit` (integer, optional): Maximum number of articles (default: 50, max: 1000)
- `offset` (integer, optional): Pagination offset (default: 0)
- `source` (string, optional): Filter by news source
- `start_date` (string, optional): Start date (ISO 8601 format)
- `end_date` (string, optional): End date (ISO 8601 format)
- `sentiment` (string, optional): Filter by sentiment (positive/negative/neutral)

**Example Request**:
```bash
curl "http://localhost:8000/articles?limit=10&source=yahoo_finance&sentiment=positive"
```

**Response**:
```json
{
  "total": 150,
  "limit": 10,
  "offset": 0,
  "articles": [
    {
      "id": 1,
      "title": "Market Rally Continues",
      "content": "...",
      "url": "https://...",
      "source": "yahoo_finance",
      "published_date": "2026-02-03T15:30:00",
      "sentiment_score": 0.75,
      "sentiment_label": "positive",
      "mentioned_stocks": ["AAPL", "TSLA"],
      "mentioned_companies": ["Apple", "Tesla"],
      "word_count": 450,
      "read_time_minutes": 2
    }
  ]
}
```

### Get Article by ID

Retrieve a specific article by its ID.

**Endpoint**: `GET /articles/{article_id}`

**Path Parameters**:
- `article_id` (integer, required): Article ID

**Example Request**:
```bash
curl http://localhost:8000/articles/1
```

**Response**:
```json
{
  "id": 1,
  "title": "Market Rally Continues",
  "content": "Full article content...",
  "summary": "Brief summary...",
  "url": "https://...",
  "source": "yahoo_finance",
  "author": "John Doe",
  "published_date": "2026-02-03T15:30:00",
  "scraped_date": "2026-02-03T16:00:00",
  "sentiment_score": 0.75,
  "sentiment_label": "positive",
  "mentioned_stocks": ["AAPL", "TSLA"],
  "mentioned_companies": ["Apple", "Tesla"],
  "mentioned_persons": ["Tim Cook", "Elon Musk"],
  "category": "Technology",
  "tags": ["stocks", "earnings"],
  "word_count": 450,
  "read_time_minutes": 2
}
```

### Search Articles

Search articles by keyword.

**Endpoint**: `GET /search`

**Query Parameters**:
- `q` (string, required): Search query
- `limit` (integer, optional): Maximum results (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

**Example Request**:
```bash
curl "http://localhost:8000/search?q=Tesla&limit=20"
```

**Response**:
```json
{
  "query": "Tesla",
  "total": 45,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": 5,
      "title": "Tesla Reports Record Earnings",
      "snippet": "...Tesla announced record quarterly earnings...",
      "url": "https://...",
      "source": "cnbc",
      "published_date": "2026-02-03T14:00:00",
      "relevance_score": 0.95
    }
  ]
}
```

### Get Statistics

Retrieve aggregated statistics.

**Endpoint**: `GET /stats`

**Query Parameters**:
- `start_date` (string, optional): Start date for statistics
- `end_date` (string, optional): End date for statistics

**Example Request**:
```bash
curl "http://localhost:8000/stats?start_date=2026-02-01&end_date=2026-02-03"
```

**Response**:
```json
{
  "period": {
    "start": "2026-02-01",
    "end": "2026-02-03"
  },
  "total_articles": 450,
  "sources": {
    "yahoo_finance": 120,
    "cnbc": 95,
    "bbc_business": 85,
    "guardian_business": 75,
    "marketwatch": 45,
    "seeking_alpha": 30
  },
  "sentiment_distribution": {
    "positive": 180,
    "neutral": 200,
    "negative": 70
  },
  "average_sentiment": 0.15,
  "top_stocks": {
    "AAPL": 45,
    "TSLA": 38,
    "MSFT": 32,
    "GOOGL": 28,
    "AMZN": 25
  },
  "articles_per_day": {
    "2026-02-01": 145,
    "2026-02-02": 155,
    "2026-02-03": 150
  }
}
```

### Get Sources

List all available news sources.

**Endpoint**: `GET /sources`

**Response**:
```json
{
  "sources": [
    {
      "name": "yahoo_finance",
      "display_name": "Yahoo Finance",
      "article_count": 1250,
      "last_scraped": "2026-02-03T16:00:00",
      "status": "active"
    },
    {
      "name": "cnbc",
      "display_name": "CNBC",
      "article_count": 980,
      "last_scraped": "2026-02-03T16:00:00",
      "status": "active"
    }
  ]
}
```

### Export Data

Export articles in various formats.

**Endpoint**: `GET /export`

**Query Parameters**:
- `format` (string, required): Export format (json/csv/xml/parquet)
- `start_date` (string, optional): Start date
- `end_date` (string, optional): End date
- `source` (string, optional): Filter by source

**Example Request**:
```bash
curl "http://localhost:8000/export?format=csv&start_date=2026-02-01" -o export.csv
```

**Response**: File download

### Get Sentiment Trends

Retrieve sentiment trends over time.

**Endpoint**: `GET /sentiment/trends`

**Query Parameters**:
- `start_date` (string, optional): Start date
- `end_date` (string, optional): End date
- `granularity` (string, optional): day/week/month (default: day)

**Example Request**:
```bash
curl "http://localhost:8000/sentiment/trends?granularity=day"
```

**Response**:
```json
{
  "granularity": "day",
  "data": [
    {
      "date": "2026-02-01",
      "average_sentiment": 0.12,
      "positive_count": 60,
      "neutral_count": 70,
      "negative_count": 15
    },
    {
      "date": "2026-02-02",
      "average_sentiment": 0.18,
      "positive_count": 65,
      "neutral_count": 68,
      "negative_count": 12
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid date format. Use ISO 8601 format (YYYY-MM-DD)",
  "status_code": 400
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Article with ID 999 not found",
  "status_code": 404
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "Database connection failed",
  "status_code": 500
}
```

## Rate Limiting

Current implementation does not enforce rate limits. For production:

- Recommended: 100 requests per minute per IP
- Implement using middleware or API gateway

## CORS

CORS is enabled for all origins in development. Configure appropriately for production.

## Pagination

For endpoints returning multiple results:

- Use `limit` and `offset` parameters
- Maximum `limit`: 1000
- Default `limit`: 50

Example:
```bash
# Page 1
curl "http://localhost:8000/articles?limit=50&offset=0"

# Page 2
curl "http://localhost:8000/articles?limit=50&offset=50"
```

## Filtering

Combine multiple filters:

```bash
curl "http://localhost:8000/articles?source=yahoo_finance&sentiment=positive&start_date=2026-02-01&limit=100"
```

## Date Formats

All dates use ISO 8601 format:
- Date: `YYYY-MM-DD` (e.g., `2026-02-03`)
- DateTime: `YYYY-MM-DDTHH:MM:SS` (e.g., `2026-02-03T15:30:00`)

## Response Formats

All responses are in JSON format with UTF-8 encoding.

## Client Examples

### Python

```python
import requests

# Get articles
response = requests.get('http://localhost:8000/articles', params={
    'limit': 10,
    'source': 'yahoo_finance'
})
articles = response.json()

# Search
response = requests.get('http://localhost:8000/search', params={
    'q': 'Tesla'
})
results = response.json()
```

### JavaScript

```javascript
// Get articles
fetch('http://localhost:8000/articles?limit=10')
  .then(response => response.json())
  .then(data => console.log(data));

// Search
fetch('http://localhost:8000/search?q=Tesla')
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL

```bash
# Get articles
curl -X GET "http://localhost:8000/articles?limit=10"

# Search
curl -X GET "http://localhost:8000/search?q=Tesla"

# Export
curl -X GET "http://localhost:8000/export?format=csv" -o export.csv
```

## WebSocket Support

Real-time updates (future feature):

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const article = JSON.parse(event.data);
  console.log('New article:', article);
};
```

## API Versioning

Current version: v1

Future versions will be accessible via:
```
http://localhost:8000/v2/articles
```

## Support

For API issues or questions:
- Check [Usage Guide](USAGE.md)
- Review [Troubleshooting Guide](TROUBLESHOOTING.md)
- Open GitHub issue

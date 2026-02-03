# Installation Guide

## System Requirements

### Minimum Requirements
- Python 3.11 or higher
- 2 GB RAM
- 500 MB disk space
- Internet connection

### Recommended Requirements
- Python 3.11+
- 4 GB RAM
- 2 GB disk space
- Stable internet connection (10+ Mbps)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/MeridianAlgo/FinDB.git
cd FinDB
```

### 2. Create Virtual Environment (Recommended)

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/MacOS
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download Required Corpora

```bash
python -m textblob.download_corpora
```

This will download the necessary NLTK data for sentiment analysis.

### 5. Verify Installation

```bash
python -c "import scraper, data_export, database; print('Installation successful')"
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory (optional):

```env
DATABASE_URL=sqlite:///financial_news.db
LOG_LEVEL=INFO
SCRAPE_INTERVAL_HOURS=24
MAX_ARTICLES_PER_SOURCE=100
DATA_RETENTION_DAYS=365
```

### Database Initialization

The database will be automatically created on first run. To manually initialize:

```python
from database import init_database
init_database()
```

## Troubleshooting

### Common Issues

#### ImportError: No module named 'X'
**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

#### NLTK Data Not Found
**Solution**: Manually download corpora
```bash
python -m textblob.download_corpora
```

#### Permission Denied on Database
**Solution**: Check file permissions
```bash
chmod 644 financial_news.db  # Linux/MacOS
```

#### SSL Certificate Errors
**Solution**: Update certificates
```bash
pip install --upgrade certifi
```

## Docker Installation (Alternative)

### Using Docker

```bash
docker build -t findb .
docker run -d -p 8000:8000 findb
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Verification

Run the test suite to verify installation:

```bash
python -m pytest tests/
```

## Next Steps

After successful installation:

1. Review [Configuration Guide](CONFIGURATION.md)
2. Read [Usage Guide](USAGE.md)
3. Check [API Documentation](API.md)
4. Review [Contributing Guidelines](../CONTRIBUTING.md)

## Support

For installation issues:
- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Open an issue on GitHub
- Contact maintainers

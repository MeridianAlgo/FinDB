# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-08-12

### Security
- Upgraded `aiohttp` 3.13.4 to 3.14.3, clearing 14 Dependabot advisories
  (1 high, 9 moderate, 4 low), including CVE-2026-69244.
- Removed the `asyncio==3.4.3` requirement. `asyncio` has been part of the
  standard library since Python 3.4; the pin installed an obsolete backport
  into site-packages where it can shadow the stdlib module.

### Fixed
- Raised the HTTP header size ceiling from 32 KB to 256 KB. Yahoo Finance's
  `Link` header varies in size per response and intermittently exceeded the
  old limit, failing the fetch and losing the article.

### Changed
- The database is no longer tracked in git. At ~5.6 KB/article with 90-day
  retention it was on course to pass GitHub's hard 100 MB per-file limit,
  beyond which pushes are rejected. It now lives in a Hugging Face dataset,
  which also makes the corpus directly consumable. See `hf_storage.py` and
  the setup steps in README.md.

### Added
- `hf_storage.py` — pull/push the database and exports to Hugging Face.
- `scripts/migrate_db_to_hf.py` — one-time cutover that verifies the upload
  by downloading it back and comparing row counts before untracking the
  database, so a failed upload cannot leave the next run with empty data.

## [1.1.0] - 2026-08-12

### Fixed
- **Corrupted content from `google_finance`.** Google News RSS links are opaque
  redirect stubs whose article pages are empty JS shells, so extraction always
  failed and the scraper stored the raw RSS markup as article content. Every
  such row also carried a sentiment score and entity lists computed over that
  string, poisoning analytics for roughly half the database.
- RSS `<summary>` values are now stripped of HTML before text cleaning. Markup
  previously collapsed into pseudo-words such as `a hrefhttps:...targetblank`.
- Articles with empty content are no longer saved (`nullable=False` does not
  reject an empty string).
- `NewsProcessor.save_articles` no longer constructs a `NewsScraper` per article.

### Added
- Content quality gate (`NewsScraper.is_usable_content`, `MIN_CONTENT_CHARS`).
  Articles that do not yield real prose are dropped rather than stored, so
  sentiment and entity analytics are never computed over URLs or markup.
- `scripts/cleanup_corrupt_rows.py` to purge affected rows (dry run by default,
  takes a timestamped backup before deleting).
- Direct feeds replacing the aggregator: CNBC finance and economy sections,
  Business Insider Markets, MarketBeat, Fortune, Forbes Business, CBC Business,
  and Nasdaq Markets. Each was validated for feed availability and full-text
  extraction before being added.

### Removed
- `google_finance` source. Resolving its redirects server-side is not possible:
  the article ID decodes to an opaque token rather than a URL, and Google's
  `batchexecute` resolution RPC rejects non-browser clients.
- 12,063 unusable rows (11,387 redirect stubs plus 676 with empty content).

## [1.0.0] - 2026-02-03

### Added
- Initial release of Financial News Scraper
- Multi-source news aggregation from 7 major sources
- Automated daily scraping via GitHub Actions
- Sentiment analysis using TextBlob
- Financial entity extraction (stocks, companies, persons)
- SQLite database with comprehensive schema
- Export functionality in 4 formats (JSON, CSV, XML, Parquet)
- RESTful API with FastAPI
- Comprehensive documentation suite
- Automated testing framework
- Data retention and cleanup policies

### Features
- **Scraping Module**
  - Async HTTP requests with aiohttp
  - RSS feed parsing with feedparser
  - Content extraction with trafilatura
  - Fallback parsing with BeautifulSoup
  - Duplicate detection via URL uniqueness
  - Error handling and retry logic

- **Database**
  - SQLite with SQLAlchemy ORM
  - Indexed queries for performance
  - Automatic schema creation
  - Data retention management
  - Scraping log tracking

- **Export System**
  - JSON: Full structured data
  - CSV: Flattened spreadsheet format
  - XML: Hierarchical structure
  - Parquet: Compressed columnar format
  - Daily summary statistics

- **API**
  - Article retrieval with filtering
  - Full-text search
  - Statistics and aggregations
  - Export endpoints
  - Pagination support

- **Automation**
  - GitHub Actions workflow
  - Daily scheduled runs (2:00 AM UTC)
  - Manual trigger capability
  - Artifact management
  - Git-based version control

### Documentation
- Installation guide
- Usage guide with examples
- Complete API reference
- System architecture documentation
- Test results and metrics
- Contributing guidelines
- Code of conduct

### Performance
- Scraping speed: 2.6 articles/second
- Success rate: 99.5%
- Export time: <5 seconds for all formats
- Memory efficient async processing

### Known Issues
- Reuters RSS feed returns 404 (URL needs update)
- Yahoo Finance header length errors on some articles
- Seeking Alpha rate limiting (403 errors)

### Dependencies
- Python 3.11+
- aiohttp 3.9.1
- feedparser 6.0.10
- trafilatura 1.6.0
- beautifulsoup4 4.12.2
- textblob 0.17.1
- sqlalchemy 2.0.23
- fastapi 0.104.1
- pandas 2.1.4
- pyarrow 14.0.1

## [Unreleased]

### Planned
- Real-time scraping with WebSockets
- Advanced ML models for entity extraction
- Multi-language support
- Cryptocurrency news sources
- Social media integration
- Data visualization dashboard
- PostgreSQL migration
- Caching layer
- GraphQL API
- Full-text search engine
- Comprehensive test suite
- Performance optimizations

---

## Version History

### Version Numbering

- **Major version** (X.0.0): Breaking changes
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

### Release Process

1. Update CHANGELOG.md
2. Update version in setup.py
3. Create git tag
4. Push to GitHub
5. Create GitHub release
6. Deploy to production

### Support Policy

- **Current version**: Full support
- **Previous major version**: Security fixes only
- **Older versions**: No support

---

For detailed commit history, see [GitHub Commits](https://github.com/MeridianAlgo/FinDB/commits/main)

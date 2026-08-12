import asyncio
import aiohttp
import feedparser
import bs4
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import logging
import json
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import time
from dataclasses import dataclass, field
from config import Config
from database import get_db, SessionLocal
from models import FinancialNews, ScrapingLog
import trafilatura
from textblob import TextBlob

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    title: str
    content: str
    url: str
    source: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)

class NewsScraper:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
    
    async def __aenter__(self):
        # Increase header limits for Yahoo Finance and other sites with large
        # cookies/headers. Yahoo's Link header (CDN preload hints) varies in
        # size per response and intermittently exceeded a 32 KB ceiling, which
        # failed the fetch and cost us the article; the ceiling is only a
        # parser bound, so keep it well clear of observed sizes.
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            max_line_size=262144,
            max_field_size=262144
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_rss_feed(self, url: str) -> Optional[Dict]:
        """Fetch and parse RSS feed"""
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    return feedparser.parse(content)
                else:
                    logger.error(f"Failed to fetch RSS feed {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            return None
    
    async def fetch_article_content(self, url: str, source_config: Dict) -> Optional[str]:
        """Fetch full article content from URL"""
        try:
            # Add referer to help with 401/blocking
            headers = self.headers.copy()
            headers['Referer'] = source_config.get('base_url', 'https://google.com')
            
            async with self.session.get(url, timeout=30, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Try trafilatura first for high quality extraction
                    traf_content = trafilatura.extract(html, include_comments=False, include_tables=False)
                    if traf_content and len(traf_content) > 100:
                        return traf_content

                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract content based on source-specific selectors
                    content_elements = soup.select(source_config.get('content_selector', 'p'))
                    if content_elements:
                        content = '\n'.join([elem.get_text(strip=True) for elem in content_elements])
                        return content
                    else:
                        # Fallback to all paragraphs
                        paragraphs = soup.find_all('p')
                        content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
                        return content
                else:
                    if response.status not in (401, 403, 404):
                        logger.error(f"Failed to fetch article {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching article content {url}: {e}")
            return None
    
    def extract_author(self, soup: BeautifulSoup, source_config: Dict) -> Optional[str]:
        """Extract author from article"""
        author_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            '.author',
            '.byline',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text(strip=True)
        
        return None
    
    def extract_publish_date(self, soup: BeautifulSoup, source_config: Dict) -> Optional[datetime]:
        """Extract publish date from article"""
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish-date"]',
            'meta[name="date"]',
            'time',
            '.date',
            '.publish-date',
            '.timestamp'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_str = ''
                if element.name == 'meta':
                    date_str = element.get('content', '').strip()
                elif element.name == 'time':
                    date_str = element.get('datetime', '') or element.get_text(strip=True)
                else:
                    date_str = element.get_text(strip=True)
                
                if date_str:
                    return self.parse_date(date_str)
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        date_formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try to extract date using regex
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\w+ \d{1,2}, \d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    return datetime.strptime(match.group(1), '%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def strip_html(self, text: str) -> str:
        """Reduce an HTML fragment to its visible text.

        RSS <summary> values are HTML, not plain text. Passing them straight to
        clean_text() used to mangle markup into pseudo-words: clean_text strips
        '/', '"' and '<' as "special characters", so an anchor tag collapsed
        into 'a hrefhttps:example.comfoo targetblankHeadlinea' and was stored as
        article content. Strip the tags first so only real prose survives.
        """
        if not text:
            return ""
        if '<' not in text:
            return text
        return BeautifulSoup(text, 'html.parser').get_text(separator=' ')

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Drop any markup before character filtering (see strip_html).
        text = self.strip_html(text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)

        return text.strip()

    # Content that is really a bare link, a redirect stub, or leftover markup
    # rather than article prose.
    _JUNK_CONTENT_PATTERNS = (
        re.compile(r'^\s*a\s+href', re.I),          # mangled anchor tag
        re.compile(r'news\.google\.com', re.I),      # Google News redirect stub
        re.compile(r'^\s*<', re.I),                  # raw markup
        re.compile(r'^\s*https?[:\s]', re.I),        # content is just a URL
    )

    def is_usable_content(self, content: str) -> bool:
        """Whether extracted content is real prose worth storing.

        Guards the database against rows whose 'content' is a URL or markup
        residue. Such rows are worse than absent: sentiment scores and entity
        extractions get computed over them and silently poison analytics.
        """
        if not content or len(content.strip()) < Config.MIN_CONTENT_CHARS:
            return False

        for pattern in self._JUNK_CONTENT_PATTERNS:
            if pattern.search(content[:200]):
                return False

        # Prose has spaces between words; a URL-ish blob does not.
        words = content.split()
        if len(words) < 20:
            return False
        if max((len(w) for w in words), default=0) > 100:
            return False

        return True


    def extract_financial_entities(self, text: str) -> Dict:
        """Extract financial entities from text"""
        # Stock ticker patterns (e.g., $AAPL, AAPL)
        stock_pattern = r'\$([A-Z]{1,5})\b|(?<!\$)([A-Z]{1,5})\b'
        stocks = list(set([match[0] or match[1] for match in re.findall(stock_pattern, text)]))
        
        # Company names (basic pattern)
        company_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+Inc\.|Corp\.|Ltd\.|LLC|PLC)?)\b'
        companies = list(set(re.findall(company_pattern, text)))
        
        # Person names (basic pattern)
        person_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        persons = list(set(re.findall(person_pattern, text)))
        
        return {
            'stocks': stocks[:10],  # Limit to top 10
            'companies': companies[:10],
            'persons': persons[:10]
        }
    
    async def scrape_source(self, source_name: str, source_config: Dict) -> Tuple[List[NewsArticle], int]:
        """Scrape news from a single source"""
        articles = []
        errors = []
        skipped = 0

        try:
            # Fetch RSS feed
            feed = await self.fetch_rss_feed(source_config['rss_url'])
            if not feed:
                return articles, 1
            
            # Process feed entries
            for entry in feed.entries[:Config.MAX_ARTICLES_PER_SOURCE]:
                try:
                    # Skip if article is from previous days (we want yesterday's news)
                    if hasattr(entry, 'published'):
                        pub_date = self.parse_date(entry.published)
                        if pub_date:
                            yesterday = datetime.now() - timedelta(days=1)
                            if pub_date.date() < yesterday.date():
                                continue
                    
                    # Extract basic info
                    title = self.clean_text(getattr(entry, 'title', ''))
                    url = getattr(entry, 'link', '')
                    summary = self.clean_text(getattr(entry, 'summary', ''))
                    
                    if not title or not url:
                        continue
                    
                    # Fetch full content
                    content = await self.fetch_article_content(url, source_config)
                    if not content:
                        content = summary  # Fallback to summary

                    # Drop rather than store unusable content. Previously an
                    # article whose page could not be extracted was saved with
                    # the raw RSS summary markup as its content, and downstream
                    # sentiment/entity analysis ran over that string.
                    if not self.is_usable_content(content):
                        logger.debug(
                            f"Skipping {url}: no usable content extracted "
                            f"({len(content or '')} chars)"
                        )
                        skipped += 1
                        continue

                    # Extract tags
                    tags = []
                    if hasattr(entry, 'tags'):
                        tags = [tag.get('term') for tag in entry.tags if tag.get('term')]

                    # Create article object
                    article = NewsArticle(
                        title=title,
                        content=content,
                        url=url,
                        source=source_name,
                        summary=summary,
                        tags=tags
                    )
                    
                    # Extract additional metadata
                    if hasattr(entry, 'author'):
                        article.author = entry.author
                    
                    if hasattr(entry, 'published'):
                        article.published_date = self.parse_date(entry.published)
                    
                    articles.append(article)
                    
                    # Add delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error processing article {getattr(entry, 'link', 'unknown')}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            if skipped:
                logger.info(
                    f"{source_name}: skipped {skipped} article(s) with no usable content"
                )

            return articles, 0 if not errors else len(errors)
            
        except Exception as e:
            error_msg = f"Error scraping source {source_name}: {e}"
            logger.error(error_msg)
            return articles, 1
    
    async def scrape_all_sources(self) -> Dict[str, Tuple[List[NewsArticle], int]]:
        """Scrape news from all configured sources"""
        results = {}
        
        # Create tasks for all sources
        tasks = []
        for source_name, source_config in Config.NEWS_SOURCES.items():
            task = asyncio.create_task(self.scrape_source(source_name, source_config))
            tasks.append((source_name, task))
        
        # Wait for all tasks to complete with timeout
        try:
            # Use asyncio.wait with timeout to prevent hanging
            done, pending = await asyncio.wait(
                [task for _, task in tasks], 
                timeout=300  # 5 minute timeout
            )
            
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Process completed tasks
            for source_name, task in tasks:
                if task in done:
                    try:
                        articles, errors = await task
                        results[source_name] = (articles, errors)
                        logger.info(f"Scraped {len(articles)} articles from {source_name} with {errors} errors")
                    except Exception as e:
                        logger.error(f"Error processing {source_name}: {e}")
                        results[source_name] = ([], 1)
                else:
                    logger.warning(f"Timeout scraping {source_name}")
                    results[source_name] = ([], 1)
                    
        except Exception as e:
            logger.error(f"Error in scrape_all_sources: {e}")
            # Return empty results for all sources
            for source_name in Config.NEWS_SOURCES.keys():
                results[source_name] = ([], 1)
        
        return results

class NewsProcessor:
    """Process and save scraped news articles"""
    
    @staticmethod
    def save_articles(articles: List[NewsArticle]) -> int:
        """Save articles to database"""
        db = SessionLocal()
        saved_count = 0
        added_urls = set()
        scraper = NewsScraper()

        try:
            # Get existing URLs from DB to avoid redundant checks
            urls_in_batch = [a.url for a in articles]
            existing_urls = set(
                url[0] for url in db.query(FinancialNews.url).filter(
                    FinancialNews.url.in_(urls_in_batch)
                ).all()
            )
            
            for article in articles:
                # Check for duplicates in current batch and existing DB
                if article.url in added_urls or article.url in existing_urls:
                    continue

                # Final guard: never persist a row whose content would poison
                # sentiment/entity analytics.
                if not scraper.is_usable_content(article.content):
                    logger.warning(
                        f"Refusing to save {article.url}: content failed quality check"
                    )
                    continue

                try:
                    # Extract financial entities
                    entities = scraper.extract_financial_entities(article.content + ' ' + article.title)

                    # Calculate sentiment
                    blob = TextBlob(article.content)
                    sentiment_score = blob.sentiment.polarity
                    sentiment_label = 'positive' if sentiment_score > 0.1 else 'negative' if sentiment_score < -0.1 else 'neutral'
                    
                    # Create database record
                    db_article = FinancialNews(
                        title=article.title,
                        content=article.content,
                        summary=article.summary,
                        url=article.url,
                        source=article.source,
                        author=article.author,
                        published_date=article.published_date or datetime.now(),
                        mentioned_stocks=json.dumps(entities['stocks']),
                        mentioned_companies=json.dumps(entities['companies']),
                        mentioned_persons=json.dumps(entities['persons']),
                        word_count=len(article.content.split()),
                        read_time_minutes=max(1, len(article.content.split()) // 200),
                        sentiment_score=sentiment_score,
                        sentiment_label=sentiment_label,
                        tags=json.dumps(article.tags)
                    )
                    
                    db.add(db_article)
                    added_urls.add(article.url)
                    saved_count += 1
                    
                    # Periodic commit to avoid massive transaction if needed,
                    # but for typical batches, one commit at end is fine.
                    # Just ensure we don't hit UNIQUE constraint if another process inserts.
                except Exception as e:
                    logger.error(f"Error processing individual article {article.url}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Saved {saved_count} new articles to database")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving articles: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    @staticmethod
    def log_scraping_session(source: str, start_time: datetime, end_time: datetime, 
                           articles_found: int, articles_saved: int, errors: List[str]):
        """Log scraping session"""
        db = SessionLocal()
        try:
            log_entry = ScrapingLog(
                source=source,
                start_time=start_time,
                end_time=end_time,
                articles_found=articles_found,
                articles_saved=articles_saved,
                errors=json.dumps(errors) if errors else None,
                success=len(errors) == 0
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging scraping session: {e}")
            db.rollback()
        finally:
            db.close()

async def main_scraping():
    """Main scraping function"""
    start_time = datetime.now()
    logger.info("Starting financial news scraping")
    
    try:
        async with NewsScraper() as scraper:
            # Scrape all sources
            results = await scraper.scrape_all_sources()
            
            total_articles = 0
            total_saved = 0
            total_errors = 0
            
            # Process results
            for source, (articles, errors) in results.items():
                total_articles += len(articles)
                
                # Save articles
                saved = NewsProcessor.save_articles(articles)
                total_saved += saved
                
                # Log session
                end_time = datetime.now()
                NewsProcessor.log_scraping_session(
                    source=source,
                    start_time=start_time,
                    end_time=end_time,
                    articles_found=len(articles),
                    articles_saved=saved,
                    errors=[f"Source errors: {errors}"] if errors > 0 else []
                )
                
                total_errors += errors
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Scraping completed in {duration:.2f} seconds")
        logger.info(f"Total articles found: {total_articles}")
        logger.info(f"Total articles saved: {total_saved}")
        logger.info(f"Total errors: {total_errors}")
        
        return {
            'success': True,
            'articles_found': total_articles,
            'articles_saved': total_saved,
            'errors': total_errors,
            'duration_seconds': duration
        }
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'duration_seconds': (datetime.now() - start_time).total_seconds()
        }

if __name__ == "__main__":
    asyncio.run(main_scraping())

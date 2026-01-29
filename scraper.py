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
from dataclasses import dataclass
from config import Config
from database import get_db, SessionLocal
from models import FinancialNews, ScrapingLog

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

class NewsScraper:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
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
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
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
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        return text.strip()
    
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
                    
                    # Create article object
                    article = NewsArticle(
                        title=title,
                        content=content,
                        url=url,
                        source=source_name,
                        summary=summary
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
        
        try:
            for article in articles:
                # Check if article already exists
                existing = db.query(FinancialNews).filter(
                    FinancialNews.url == article.url
                ).first()
                
                if existing:
                    continue
                
                # Extract financial entities
                entities = NewsScraper().extract_financial_entities(article.content + ' ' + article.title)
                
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
                    read_time_minutes=max(1, len(article.content.split()) // 200)
                )
                
                db.add(db_article)
                saved_count += 1
            
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

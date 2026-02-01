from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
import time
import json
from io import BytesIO
from sqlalchemy.orm import Session

from config import Config
from database import get_db, SessionLocal
from models import FinancialNews, ScrapingLog, APIUsage
from scraper import main_scraping
from data_export import DataExporter, export_daily_news, export_weekly_news

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Financial News API",
    description="API for accessing scraped financial news data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    summary: Optional[str]
    url: str
    source: str
    author: Optional[str]
    published_date: datetime
    scraped_date: datetime
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    mentioned_stocks: List[str]
    mentioned_companies: List[str]
    mentioned_persons: List[str]
    category: Optional[str]
    subcategory: Optional[str]
    tags: List[str]
    word_count: int
    read_time_minutes: int

class ScrapingStatusResponse(BaseModel):
    success: bool
    message: str
    last_scrape: Optional[datetime]
    total_articles: int
    articles_today: int

class ExportRequest(BaseModel):
    format: str = Field(..., regex="^(json|csv|xml|parquet)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: Optional[str] = None
    limit: Optional[int] = Field(None, ge=1, le=10000)

class SearchRequest(BaseModel):
    query: str
    source: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)

# Middleware for API usage tracking
@app.middleware("http")
async def track_api_usage(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Log API usage
    process_time = int((time.time() - start_time) * 1000)
    
    db = SessionLocal()
    try:
        usage = APIUsage(
            endpoint=str(request.url.path),
            method=request.method,
            timestamp=datetime.now(),
            response_time_ms=process_time,
            status_code=response.status_code,
            user_agent=request.headers.get("user-agent", ""),
            ip_address=request.client.host
        )
        db.add(usage)
        db.commit()
    except Exception as e:
        logger.error(f"Error tracking API usage: {e}")
        db.rollback()
    finally:
        db.close()
    
    return response

# Helper functions
def log_api_usage(endpoint: str, method: str, response_time_ms: int, status_code: int):
    """Log API usage to database"""
    db = SessionLocal()
    try:
        usage = APIUsage(
            endpoint=endpoint,
            method=method,
            timestamp=datetime.now(),
            response_time_ms=response_time_ms,
            status_code=status_code
        )
        db.add(usage)
        db.commit()
    except Exception as e:
        logger.error(f"Error logging API usage: {e}")
    finally:
        db.close()

# API Endpoints

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Financial News API",
        "version": "1.0.0",
        "description": "API for accessing scraped financial news data",
        "endpoints": {
            "articles": "/api/articles",
            "search": "/api/search",
            "export": "/api/export",
            "scraping": "/api/scraping",
            "stats": "/api/stats",
            "sources": "/api/sources"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/api/articles", response_model=List[ArticleResponse])
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get articles with optional filtering"""
    start_time = time.time()
    
    try:
        query = db.query(FinancialNews)
        
        if source:
            query = query.filter(FinancialNews.source == source)
        
        if start_date:
            query = query.filter(FinancialNews.published_date >= start_date)
        
        if end_date:
            query = query.filter(FinancialNews.published_date <= end_date)
        
        articles = query.order_by(FinancialNews.published_date.desc()).offset(skip).limit(limit).all()
        
        # Convert to response format
        response_articles = []
        for article in articles:
            response_articles.append(ArticleResponse(
                id=article.id,
                title=article.title,
                content=article.content,
                summary=article.summary,
                url=article.url,
                source=article.source,
                author=article.author,
                published_date=article.published_date,
                scraped_date=article.scraped_date,
                sentiment_score=article.sentiment_score,
                sentiment_label=article.sentiment_label,
                mentioned_stocks=json.loads(article.mentioned_stocks) if article.mentioned_stocks else [],
                mentioned_companies=json.loads(article.mentioned_companies) if article.mentioned_companies else [],
                mentioned_persons=json.loads(article.mentioned_persons) if article.mentioned_persons else [],
                category=article.category,
                subcategory=article.subcategory,
                tags=json.loads(article.tags) if article.tags else [],
                word_count=article.word_count,
                read_time_minutes=article.read_time_minutes
            ))
        
        log_api_usage("/api/articles", "GET", int((time.time() - start_time) * 1000), 200)
        return response_articles
        
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get a specific article by ID"""
    start_time = time.time()
    
    try:
        article = db.query(FinancialNews).filter(FinancialNews.id == article_id).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        response_article = ArticleResponse(
            id=article.id,
            title=article.title,
            content=article.content,
            summary=article.summary,
            url=article.url,
            source=article.source,
            author=article.author,
            published_date=article.published_date,
            scraped_date=article.scraped_date,
            sentiment_score=article.sentiment_score,
            sentiment_label=article.sentiment_label,
            mentioned_stocks=json.loads(article.mentioned_stocks) if article.mentioned_stocks else [],
            mentioned_companies=json.loads(article.mentioned_companies) if article.mentioned_companies else [],
            mentioned_persons=json.loads(article.mentioned_persons) if article.mentioned_persons else [],
            category=article.category,
            subcategory=article.subcategory,
            tags=json.loads(article.tags) if article.tags else [],
            word_count=article.word_count,
            read_time_minutes=article.read_time_minutes
        )
        
        log_api_usage(f"/api/articles/{article_id}", "GET", int((time.time() - start_time) * 1000), 200)
        return response_article
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=List[ArticleResponse])
async def search_articles(search_request: SearchRequest, db: Session = Depends(get_db)):
    """Search articles by text query"""
    start_time = time.time()
    
    try:
        # Build search query
        query = db.query(FinancialNews)
        
        # Text search (simple implementation)
        if search_request.query:
            search_filter = (
                FinancialNews.title.contains(search_request.query) |
                FinancialNews.content.contains(search_request.query) |
                FinancialNews.summary.contains(search_request.query)
            )
            query = query.filter(search_filter)
        
        if search_request.source:
            query = query.filter(FinancialNews.source == search_request.source)
        
        if search_request.start_date:
            query = query.filter(FinancialNews.published_date >= search_request.start_date)
        
        if search_request.end_date:
            query = query.filter(FinancialNews.published_date <= search_request.end_date)
        
        articles = query.order_by(FinancialNews.published_date.desc()).limit(search_request.limit).all()
        
        # Convert to response format
        response_articles = []
        for article in articles:
            response_articles.append(ArticleResponse(
                id=article.id,
                title=article.title,
                content=article.content,
                summary=article.summary,
                url=article.url,
                source=article.source,
                author=article.author,
                published_date=article.published_date,
                scraped_date=article.scraped_date,
                sentiment_score=article.sentiment_score,
                sentiment_label=article.sentiment_label,
                mentioned_stocks=json.loads(article.mentioned_stocks) if article.mentioned_stocks else [],
                mentioned_companies=json.loads(article.mentioned_companies) if article.mentioned_companies else [],
                mentioned_persons=json.loads(article.mentioned_persons) if article.mentioned_persons else [],
                category=article.category,
                subcategory=article.subcategory,
                tags=json.loads(article.tags) if article.tags else [],
                word_count=article.word_count,
                read_time_minutes=article.read_time_minutes
            ))
        
        log_api_usage("/api/search", "POST", int((time.time() - start_time) * 1000), 200)
        return response_articles
        
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export")
async def export_data(export_request: ExportRequest):
    """Export data in various formats"""
    start_time = time.time()
    
    try:
        # Set default date range if not provided
        if not export_request.start_date:
            export_request.start_date = datetime.now() - timedelta(days=1)
        if not export_request.end_date:
            export_request.end_date = datetime.now()
        
        # Export data
        exported_data = DataExporter.export_date_range(
            start_date=export_request.start_date,
            end_date=export_request.end_date,
            format=export_request.format,
            source=export_request.source,
            limit=export_request.limit
        )
        
        if not exported_data:
            raise HTTPException(status_code=404, detail="No data found for the specified criteria")
        
        # Prepare response
        media_types = {
            "json": "application/json",
            "csv": "text/csv",
            "xml": "application/xml",
            "parquet": "application/octet-stream"
        }
        
        filename = f"financial_news_{export_request.start_date.strftime('%Y-%m-%d')}_to_{export_request.end_date.strftime('%Y-%m-%d')}.{export_request.format}"
        
        log_api_usage("/api/export", "POST", int((time.time() - start_time) * 1000), 200)
        
        if export_request.format == "parquet":
            return StreamingResponse(
                BytesIO(exported_data.encode('latin1')),
                media_type=media_types[export_request.format],
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            return Response(
                content=exported_data,
                media_type=media_types[export_request.format],
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/yesterday")
async def export_yesterday(format: str = Query("json", regex="^(json|csv|xml|parquet)$")):
    """Export yesterday's news"""
    start_time = time.time()
    
    try:
        exported_data = DataExporter.export_yesterday_news(format)
        
        if not exported_data:
            raise HTTPException(status_code=404, detail="No articles found for yesterday")
        
        media_types = {
            "json": "application/json",
            "csv": "text/csv",
            "xml": "application/xml",
            "parquet": "application/octet-stream"
        }
        
        yesterday = datetime.now().date() - timedelta(days=1)
        filename = f"financial_news_{yesterday.strftime('%Y-%m-%d')}.{format}"
        
        log_api_usage("/api/export/yesterday", "GET", int((time.time() - start_time) * 1000), 200)
        
        if format == "parquet":
            return StreamingResponse(
                BytesIO(exported_data.encode('latin1')),
                media_type=media_types[format],
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            return Response(
                content=exported_data,
                media_type=media_types[format],
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
    except Exception as e:
        logger.error(f"Error exporting yesterday's news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scraping/trigger")
async def trigger_scraping(background_tasks: BackgroundTasks):
    """Trigger manual scraping"""
    start_time = time.time()
    
    try:
        # Run scraping in background
        background_tasks.add_task(asyncio.run, main_scraping())
        
        log_api_usage("/api/scraping/trigger", "POST", int((time.time() - start_time) * 1000), 200)
        
        return {
            "message": "Scraping started in background",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error triggering scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scraping/status", response_model=ScrapingStatusResponse)
async def get_scraping_status(db: Session = Depends(get_db)):
    """Get scraping status and statistics"""
    start_time = time.time()
    
    try:
        # Get last scraping log
        last_scrape = db.query(ScrapingLog).order_by(ScrapingLog.start_time.desc()).first()
        
        # Get total articles count
        total_articles = db.query(FinancialNews).count()
        
        # Get today's articles
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        articles_today = db.query(FinancialNews).filter(
            FinancialNews.published_date >= today_start
        ).count()
        
        status = ScrapingStatusResponse(
            success=last_scrape.success if last_scrape else False,
            message="Last scraping completed successfully" if (last_scrape and last_scrape.success) else "No recent scraping",
            last_scrape=last_scrape.start_time if last_scrape else None,
            total_articles=total_articles,
            articles_today=articles_today
        )
        
        log_api_usage("/api/scraping/status", "GET", int((time.time() - start_time) * 1000), 200)
        return status
        
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    start_time = time.time()
    
    try:
        stats = DataExporter.get_export_stats()
        
        log_api_usage("/api/stats", "GET", int((time.time() - start_time) * 1000), 200)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sources")
async def get_sources():
    """Get available news sources"""
    start_time = time.time()
    
    try:
        sources = list(Config.NEWS_SOURCES.keys())
        
        log_api_usage("/api/sources", "GET", int((time.time() - start_time) * 1000), 200)
        return {"sources": sources}
        
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Run the API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
        log_level=Config.LOG_LEVEL.lower()
    )

import json
import csv
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import FinancialNews
import io
import logging

logger = logging.getLogger(__name__)

class DataExporter:
    """Export financial news data in various machine-readable formats"""
    
    @staticmethod
    def get_articles_query(db: Session, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         source: Optional[str] = None,
                         limit: Optional[int] = None):
        """Build query for articles with optional filters"""
        query = db.query(FinancialNews)
        
        if start_date:
            query = query.filter(FinancialNews.published_date >= start_date)
        
        if end_date:
            query = query.filter(FinancialNews.published_date <= end_date)
        
        if source:
            query = query.filter(FinancialNews.source == source)
        
        query = query.order_by(FinancialNews.published_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query
    
    @staticmethod
    def article_to_dict(article: FinancialNews) -> Dict[str, Any]:
        """Convert article object to dictionary"""
        return {
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'summary': article.summary,
            'url': article.url,
            'source': article.source,
            'author': article.author,
            'published_date': article.published_date.isoformat() if article.published_date else None,
            'scraped_date': article.scraped_date.isoformat() if article.scraped_date else None,
            'sentiment_score': article.sentiment_score,
            'sentiment_label': article.sentiment_label,
            'mentioned_stocks': json.loads(article.mentioned_stocks) if article.mentioned_stocks else [],
            'mentioned_companies': json.loads(article.mentioned_companies) if article.mentioned_companies else [],
            'mentioned_persons': json.loads(article.mentioned_persons) if article.mentioned_persons else [],
            'category': article.category,
            'subcategory': article.subcategory,
            'tags': json.loads(article.tags) if article.tags else [],
            'word_count': article.word_count,
            'read_time_minutes': article.read_time_minutes,
            'is_duplicate': article.is_duplicate,
            'duplicate_of_id': article.duplicate_of_id
        }
    
    @staticmethod
    def export_to_json(articles: List[FinancialNews], filename: Optional[str] = None) -> str:
        """Export articles to JSON format"""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_articles': len(articles),
            'articles': [DataExporter.article_to_dict(article) for article in articles]
        }
        
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"Exported {len(articles)} articles to JSON file: {filename}")
        
        return json_str
    
    @staticmethod
    def export_to_csv(articles: List[FinancialNews], filename: Optional[str] = None) -> str:
        """Export articles to CSV format"""
        if not articles:
            return ""
        
        # Convert articles to dictionaries
        data = [DataExporter.article_to_dict(article) for article in articles]
        
        # Flatten nested fields for CSV
        flattened_data = []
        for item in data:
            flat_item = item.copy()
            flat_item['mentioned_stocks'] = ';'.join(flat_item['mentioned_stocks'])
            flat_item['mentioned_companies'] = ';'.join(flat_item['mentioned_companies'])
            flat_item['mentioned_persons'] = ';'.join(flat_item['mentioned_persons'])
            flat_item['tags'] = ';'.join(flat_item['tags'])
            flattened_data.append(flat_item)
        
        # Create CSV string
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=flattened_data[0].keys())
        writer.writeheader()
        writer.writerows(flattened_data)
        csv_str = output.getvalue()
        output.close()
        
        if filename:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_str)
            logger.info(f"Exported {len(articles)} articles to CSV file: {filename}")
        
        return csv_str
    
    @staticmethod
    def export_to_xml(articles: List[FinancialNews], filename: Optional[str] = None) -> str:
        """Export articles to XML format"""
        root = ET.Element('financial_news')
        root.set('export_timestamp', datetime.now().isoformat())
        root.set('total_articles', str(len(articles)))
        
        for article in articles:
            article_dict = DataExporter.article_to_dict(article)
            article_elem = ET.SubElement(root, 'article')
            
            for key, value in article_dict.items():
                if value is not None:
                    elem = ET.SubElement(article_elem, key)
                    if isinstance(value, list):
                        elem.text = ';'.join(str(v) for v in value)
                    else:
                        elem.text = str(value)
        
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            logger.info(f"Exported {len(articles)} articles to XML file: {filename}")
        
        return xml_str
    
    @staticmethod
    def export_to_parquet(articles: List[FinancialNews], filename: Optional[str] = None) -> bytes:
        """Export articles to Parquet format"""
        data = [DataExporter.article_to_dict(article) for article in articles]
        df = pd.DataFrame(data)
        
        # Handle list columns for Parquet
        for col in ['mentioned_stocks', 'mentioned_companies', 'mentioned_persons', 'tags']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: ';'.join(x) if isinstance(x, list) else x)
        
        # Convert to bytes
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        parquet_bytes = buffer.getvalue()
        buffer.close()
        
        if filename:
            with open(filename, 'wb') as f:
                f.write(parquet_bytes)
            logger.info(f"Exported {len(articles)} articles to Parquet file: {filename}")
        
        return parquet_bytes
    
    @staticmethod
    def export_yesterday_news(format: str = 'json', filename: Optional[str] = None) -> str:
        """Export yesterday's news in specified format"""
        db = SessionLocal()
        try:
            # Get yesterday's date range
            yesterday = datetime.now().date() - timedelta(days=1)
            start_date = datetime.combine(yesterday, datetime.min.time())
            end_date = datetime.combine(yesterday, datetime.max.time())
            
            # Query articles
            articles = DataExporter.get_articles_query(
                db, start_date=start_date, end_date=end_date
            ).all()
            
            if not articles:
                logger.warning("No articles found for yesterday")
                return ""
            
            # Export in requested format
            if format.lower() == 'json':
                return DataExporter.export_to_json(articles, filename)
            elif format.lower() == 'csv':
                return DataExporter.export_to_csv(articles, filename)
            elif format.lower() == 'xml':
                return DataExporter.export_to_xml(articles, filename)
            elif format.lower() == 'parquet':
                if filename:
                    DataExporter.export_to_parquet(articles, filename)
                    return filename
                else:
                    return DataExporter.export_to_parquet(articles).decode('latin1')
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting yesterday's news: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def export_date_range(start_date: datetime, end_date: datetime, 
                         format: str = 'json', filename: Optional[str] = None,
                         source: Optional[str] = None, limit: Optional[int] = None) -> str:
        """Export news for a specific date range"""
        db = SessionLocal()
        try:
            articles = DataExporter.get_articles_query(
                db, start_date=start_date, end_date=end_date, 
                source=source, limit=limit
            ).all()
            
            if not articles:
                logger.warning(f"No articles found for date range {start_date} to {end_date}")
                return ""
            
            # Export in requested format
            if format.lower() == 'json':
                return DataExporter.export_to_json(articles, filename)
            elif format.lower() == 'csv':
                return DataExporter.export_to_csv(articles, filename)
            elif format.lower() == 'xml':
                return DataExporter.export_to_xml(articles, filename)
            elif format.lower() == 'parquet':
                if filename:
                    DataExporter.export_to_parquet(articles, filename)
                    return filename
                else:
                    return DataExporter.export_to_parquet(articles).decode('latin1')
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting date range news: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_export_stats() -> Dict[str, Any]:
        """Get statistics about exported data"""
        db = SessionLocal()
        try:
            total_articles = db.query(FinancialNews).count()
            
            # Articles by source
            source_stats = db.query(
                FinancialNews.source,
                db.func.count(FinancialNews.id).label('count')
            ).group_by(FinancialNews.source).all()
            
            # Articles by date (last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_articles = db.query(FinancialNews).filter(
                FinancialNews.published_date >= seven_days_ago
            ).count()
            
            # Date range of articles
            oldest = db.query(db.func.min(FinancialNews.published_date)).scalar()
            newest = db.query(db.func.max(FinancialNews.published_date)).scalar()
            
            return {
                'total_articles': total_articles,
                'articles_by_source': dict(source_stats),
                'articles_last_7_days': recent_articles,
                'date_range': {
                    'oldest': oldest.isoformat() if oldest else None,
                    'newest': newest.isoformat() if newest else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting export stats: {e}")
            raise
        finally:
            db.close()

# Convenience functions for common export tasks
def export_daily_news(format: str = 'json', output_dir: str = 'exports') -> str:
    """Export yesterday's news with automatic filename"""
    from pathlib import Path
    import os
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate filename
    yesterday = datetime.now().date() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')
    filename = os.path.join(output_dir, f'financial_news_{date_str}.{format}')
    
    return DataExporter.export_yesterday_news(format, filename)

def export_weekly_news(format: str = 'json', output_dir: str = 'exports') -> str:
    """Export last 7 days of news"""
    from pathlib import Path
    import os
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate filename
    today = datetime.now().date()
    date_str = today.strftime('%Y-%m-%d')
    filename = os.path.join(output_dir, f'financial_news_week_{date_str}.{format}')
    
    # Calculate date range
    end_date = datetime.combine(today, datetime.max.time())
    start_date = end_date - timedelta(days=7)
    
    return DataExporter.export_date_range(start_date, end_date, format, filename)

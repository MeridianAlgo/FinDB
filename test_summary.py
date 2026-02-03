from datetime import datetime, timedelta
from database import SessionLocal
from models import FinancialNews
import json

db = SessionLocal()
try:
    yesterday = datetime.now().date() - timedelta(days=1)
    start_date = datetime.combine(yesterday, datetime.min.time())
    end_date = datetime.combine(yesterday, datetime.max.time())
    
    articles = db.query(FinancialNews).filter(
        FinancialNews.published_date >= start_date,
        FinancialNews.published_date <= end_date
    ).all()
    
    summary = {
        'date': yesterday.isoformat(),
        'total_articles': len(articles),
        'sources': {},
        'top_stocks': {},
        'sample_titles': []
    }
    
    for article in articles:
        source = article.source
        if source not in summary['sources']:
            summary['sources'][source] = 0
        summary['sources'][source] += 1
        
        if article.mentioned_stocks:
            stocks = json.loads(article.mentioned_stocks)
            for stock in stocks:
                if stock not in summary['top_stocks']:
                    summary['top_stocks'][stock] = 0
                summary['top_stocks'][stock] += 1
        
        if len(summary['sample_titles']) < 5:
            summary['sample_titles'].append(article.title)
    
    summary['top_stocks'] = dict(sorted(summary['top_stocks'].items(), key=lambda x: x[1], reverse=True)[:10])
    
    with open('exports/daily_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Daily summary: {summary['total_articles']} articles from {len(summary['sources'])} sources")
    print(f"\nTop 5 stocks mentioned: {list(summary['top_stocks'].keys())[:5]}")
    print(f"\nSample titles:")
    for title in summary['sample_titles']:
        print(f"  - {title}")
finally:
    db.close()

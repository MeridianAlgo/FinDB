import requests
import feedparser
from datetime import datetime, timedelta
import json

def test_simple_rss():
    """Test simple RSS scraping without full article content"""
    
    # Test with a simple RSS feed that should work
    rss_urls = [
        "https://finance.yahoo.com/news/rssindex",
        "https://www.marketwatch.com/rss/topstories"
    ]
    
    articles = []
    
    for rss_url in rss_urls:
        try:
            print(f"Testing RSS feed: {rss_url}")
            
            # Fetch RSS feed
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=30)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:5]:  # Just get 5 articles for testing
                    article = {
                        'title': getattr(entry, 'title', 'No title'),
                        'url': getattr(entry, 'link', ''),
                        'summary': getattr(entry, 'summary', ''),
                        'published': getattr(entry, 'published', ''),
                        'source': rss_url.split('/')[2]  # Extract domain
                    }
                    articles.append(article)
                    print(f"  - {article['title'][:50]}...")
                    
            else:
                print(f"  Failed with HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    # Save test results
    if articles:
        with open('test_articles.json', 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'total_articles': len(articles),
                'articles': articles
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nSuccessfully scraped {len(articles)} articles!")
        print("Results saved to test_articles.json")
    else:
        print("No articles were successfully scraped.")

if __name__ == "__main__":
    test_simple_rss()

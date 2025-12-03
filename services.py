import sys
try:
    import cgi
except ImportError:
    import html
    class cgi:
        @staticmethod
        def escape(s, quote=False):
            return html.escape(s, quote=quote)
    sys.modules['cgi'] = cgi

import feedparser
import requests
from bs4 import BeautifulSoup
import boto3
import json
import time
import logging
from datetime import datetime, timedelta
from database import get_db, Article, Feed, Topic, Category

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSSFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_feed(self, feed_url):
        try:
            feed = feedparser.parse(feed_url)
            return feed.entries
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []
    
    def get_article_content(self, entry):
        return getattr(entry, 'description', '') or getattr(entry, 'summary', '')

class AIService:
    def __init__(self, api_key=None):
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def analyze_article(self, title, author, content, url, categories):
        categories_list = [cat.name for cat in categories]
        categories_text = ", ".join(categories_list)
        
        prompt = f"""Create executive briefing from this article. Extract comprehensive facts and direct quotes.

Title: {title}
Content: {content[:2500]}

Provide up to 5 bullet points with:
- Key facts with exact numbers, names, dates
- Direct quotes from officials/sources (use exact wording)
- Important context and implications
- No repetitive information
- Include more substantive content

Categorize: {categories_text}

Return JSON:
{{"highlights": ["Fact with quote 1", "Fact with quote 2", "Fact 3", "Fact 4", "Fact 5"], "category": "category_name"}}"""
        
        try:
            payload = {
                "max_tokens": 1200,
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": prompt}]
            }
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(payload).encode('utf-8')
            )
            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text']
            result = json.loads(response_text)
            
            if isinstance(result, dict):
                highlights = result.get("highlights", [])
                if isinstance(highlights, list):
                    # Clean up redundant bullets and remove duplicates
                    cleaned_highlights = []
                    seen_content = set()
                    for h in highlights:
                        # Remove existing bullet if present
                        clean_h = h.strip()
                        if clean_h.startswith('•'):
                            clean_h = clean_h[1:].strip()
                        
                        # Check for duplicates using normalized text
                        normalized = clean_h.lower().replace('"', '').replace("'", '').strip()
                        if normalized and normalized not in seen_content:
                            seen_content.add(normalized)
                            cleaned_highlights.append(clean_h)
                    
                    highlights_text = "\n".join([f"• {h}" for h in cleaned_highlights])
                else:
                    highlights_text = str(highlights)
                    
                return {
                    "summary": highlights_text,
                    "quotes": "",
                    "category": result.get("category", "")
                }
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
        return {"summary": "Analysis failed", "quotes": "", "category": ""}

class NewsProcessor:
    def __init__(self, api_key=None):
        self.rss_fetcher = RSSFetcher()
        self.ai_service = AIService(api_key)
        self.processing = False
    
    def cleanup_old_articles(self):
        db = get_db()
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_articles = db.query(Article).filter(Article.created_at < cutoff_time).all()
            count = len(old_articles)
            for article in old_articles:
                db.delete(article)
            db.commit()
            if count > 0:
                print(f"Cleaned up {count} articles older than 24 hours")
            return count
        finally:
            db.close()
    
    def clear_all_articles(self):
        db = get_db()
        try:
            count = db.query(Article).count()
            db.query(Article).delete()
            db.commit()
            print(f"Cleared all {count} articles from database")
            return count
        finally:
            db.close()
    
    def process_feeds(self):
        if self.processing:
            return "Already processing"
        
        self.processing = True
        try:
            self.cleanup_old_articles()
            
            db = get_db()
            feeds = db.query(Feed).filter(Feed.active == True).all()
            categories = db.query(Category).filter(Category.active == True).all()
            
            if not categories:
                return "No active categories found"
            
            cutoff_time = datetime.now() - timedelta(hours=24)
            processed_count = 0
            total_entries = 0
            
            print(f"\n=== Starting news processing ===")
            print(f"Active feeds: {len(feeds)}")
            print(f"Active categories: {len(categories)}")
            
            processed_urls = set()
            
            for feed in feeds:
                print(f"\nProcessing feed: {feed.name}")
                entries = self.rss_fetcher.fetch_feed(feed.url)
                print(f"Found {len(entries)} entries in feed")
                total_entries += len(entries)
                
                for entry in entries:
                    try:
                        entry_link = getattr(entry, 'link', '')
                        entry_title = getattr(entry, 'title', 'Untitled')
                        entry_author = getattr(entry, 'author', '')
                        
                        published_date = datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            try:
                                published_date = datetime(*entry.published_parsed[:6])
                            except:
                                pass
                        
                        if published_date < cutoff_time:
                            continue
                        
                        if not entry_link or entry_link in processed_urls:
                            continue
                        
                        processed_urls.add(entry_link)
                        print(f"Processing: {entry_title[:60]}...")
                        
                        existing = db.query(Article).filter(Article.url == entry_link).first()
                        if existing:
                            print(f"  -> Already exists, skipping")
                            continue
                        
                        content = self.rss_fetcher.get_article_content(entry)
                        if not content:
                            continue
                        
                        print(f"  -> Analyzing with AI...")
                        time.sleep(1)
                        analysis = self.ai_service.analyze_article(entry_title, entry_author, content, entry_link, categories)
                        
                        # Skip articles with failed analysis
                        if analysis.get("summary", "") == "Analysis failed":
                            print(f"  -> Skipping due to AI analysis failure")
                            continue
                        
                        category_name = analysis.get("category", "")
                        print(f"  -> Category: {category_name}")
                        
                        category = next((c for c in categories if c.name == category_name), categories[0]) if category_name else categories[0]
                            
                        article = Article(
                            title=entry_title,
                            url=entry_link,
                            content=content,
                            summary=analysis.get("summary", ""),
                            author=entry_author,
                            feed_id=feed.id,
                            published_date=published_date,
                            category_name=category.name,
                            category_color=category.color
                        )
                        
                        db.add(article)
                        db.commit()
                        processed_count += 1
                        print(f"  -> ✓ Article saved! Category: {category.name} ({processed_count} total)")
                    
                    except Exception as entry_error:
                        logger.error(f"Error processing entry: {entry_error}")
                        continue
            
            db.close()
            print(f"\n=== Processing complete ===")
            print(f"Total entries processed: {total_entries}")
            print(f"Relevant articles saved: {processed_count}")
            return f"Processed {processed_count} relevant articles from {total_entries} entries"
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return f"Error: {e}"
        finally:
            self.processing = False
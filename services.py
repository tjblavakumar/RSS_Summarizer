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
import botocore.exceptions
import json
import os
import re
import time
import logging
from datetime import datetime, timedelta
from database import get_db, Article, Feed, Topic

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
    
    def scrape_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted tags
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # Extract main content
            content = soup.get_text(separator=' ', strip=True)
            return content[:3000]  # Limit for token usage
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ""
    
    def get_article_content(self, entry):
        description = getattr(entry, 'description', '')
        if len(description) >= 500:
            return description
        
        # Scrape if description is too short
        url = getattr(entry, 'link', '')
        if url:
            scraped = self.scrape_content(url)
            return scraped if scraped else description
        return description

class AIService:
    def __init__(self, api_key=None):
        # AWS Bedrock doesn't use API keys directly, it uses AWS credentials
        # Make sure you have AWS credentials configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        # Using Claude 3 Haiku model which is faster and more accessible
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def analyze_article(self, content, topics):
        topics_list = [f"{topic.name}: {topic.keywords}" for topic in topics]
        topics_text = ", ".join(topics_list)
        
        prompt = f"""Analyze this article content against these topics: {topics_text}

    Article: {content[:2000]}

    Return ONLY a valid JSON object with no additional text:
    {{
        "summary": "string (3-4 bullet points using • character)",
        "topic_scores": {{
            "{topics[0].name}": int (0-100),
            "{topics[1].name if len(topics) > 1 else 'example'}": int (0-100)
        }}
    }}
    
    Include ALL topics in topic_scores with their relevancy percentages."""
        
        try:
            logger.debug("Invoking model %s", self.model_id)
            # Build the provider-specific payload. Anthropic/Claude models expect a "messages" array (role/content),
            # while other providers may expect a single "input" string. To increase compatibility, use the messages
            # format if the model id contains 'anthropic'. Include the provider version in plain YYYY-MM-DD format.
            payload = {
                "max_tokens": 500
            }
            if 'anthropic' in self.model_id:
                # Anthropic models require anthropic_version field
                anthropic_version = os.environ.get('ANTHROPIC_PROVIDER_VERSION', 'bedrock-2023-05-31')
                payload['anthropic_version'] = anthropic_version
                payload['messages'] = [{"role": "user", "content": prompt}]
                logger.debug('Using Anthropic provider version: %s', anthropic_version)
            else:
                payload['input'] = prompt

            logger.debug('AI payload prepared: %s', json.dumps({k: (v if k != 'messages' else '[... messages ...]') for k, v in payload.items()}))
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(payload).encode('utf-8')
            )
            
            logger.debug("AI invocation response metadata: %s", response.get('ResponseMetadata', {}))
            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text']
            
            # Parse JSON from response
            result = json.loads(response_text)
            
            # Handle list response (extract first item if it's a list)
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            # Ensure result is a dictionary with required keys
            if isinstance(result, dict):
                summary = result.get("summary", "")
                # Convert list to string if needed
                if isinstance(summary, list):
                    summary = "\n".join(summary)
                
                topic_scores = result.get("topic_scores", {})
                # Ensure all scores are integers
                for topic_name in topic_scores:
                    try:
                        topic_scores[topic_name] = int(topic_scores[topic_name])
                    except (ValueError, TypeError):
                        topic_scores[topic_name] = 0
                
                return {
                    "summary": str(summary),
                    "topic_scores": topic_scores
                }
            else:
                logger.error(f"AI returned non-dict response: {type(result)}")
                return {"summary": "Invalid response format", "topic_scores": {}}
        except json.JSONDecodeError as e:
            logger.error(f"AI analysis JSON decode error: {e}")
            return {"summary": "JSON parsing failed", "topic_scores": {}}
        except Exception as e:
            # Include the exception type and message for better diagnostics
            # For botocore ClientError, include the error response body
            try:
                error_response = getattr(e, 'response', {})
                logger.error(f"AI analysis error: {type(e).__name__}: {e}; response: {error_response}")
            except Exception:
                logger.error(f"AI analysis error: {type(e).__name__}: {e}")
            return {"summary": "Analysis failed", "topic_scores": {}}

class NewsProcessor:
    def __init__(self, api_key=None):
        self.rss_fetcher = RSSFetcher()
        self.ai_service = AIService(api_key)
        self.processing = False
        self.refresh_callback = None
    
    def set_refresh_callback(self, callback):
        self.refresh_callback = callback
    
    def cleanup_old_articles(self):
        """Delete articles older than 24 hours"""
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
        """Delete all articles from the database"""
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
            # Clean up old articles first
            self.cleanup_old_articles()
            
            db = get_db()
            feeds = db.query(Feed).filter(Feed.active == True).all()
            topics = db.query(Topic).filter(Topic.active == True).all()
            
            if not topics:
                return "No active topics found"
            
            topics_text = ", ".join([f"{t.name}: {t.keywords}" for t in topics])
            processed_count = 0
            total_entries = 0
            
            print(f"\n=== Starting news processing ===")
            print(f"Active feeds: {len(feeds)}")
            print(f"Active topics: {len(topics)}")
            
            for feed in feeds:
                print(f"\nProcessing feed: {feed.name}")
                entries = self.rss_fetcher.fetch_feed(feed.url)
                print(f"Found {len(entries)} entries in feed")
                total_entries += len(entries)
                
                for entry in entries:
                    try:
                        # Safely get entry attributes
                        entry_link = getattr(entry, 'link', '')
                        entry_title = getattr(entry, 'title', 'Untitled')
                        entry_author = getattr(entry, 'author', '') or getattr(entry, 'dc_creator', '')
                        
                        # Parse published date
                        published_date = datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            try:
                                published_date = datetime(*entry.published_parsed[:6])
                            except:
                                pass
                        
                        if not entry_link:
                            continue
                        
                        print(f"Processing: {entry_title[:60]}...")
                        
                        # Check if article already exists
                        existing = db.query(Article).filter(Article.url == entry_link).first()
                        if existing:
                            print(f"  -> Already exists, skipping")
                            continue
                        
                        content = self.rss_fetcher.get_article_content(entry)
                        if not content:
                            continue
                        
                        # AI analysis with rate limiting
                        print(f"  -> Analyzing with AI...")
                        time.sleep(2)  # Rate limit protection
                        analysis = self.ai_service.analyze_article(content, topics)
                        
                        # Ensure analysis is a dict
                        if not isinstance(analysis, dict):
                            logger.warning(f"Invalid analysis response for {entry_title}")
                            continue
                        
                        topic_scores = analysis.get("topic_scores", {})
                        print(f"  -> Topic scores: {topic_scores}")
                        
                        # Check if any topic score is above 75
                        max_score = max(topic_scores.values()) if topic_scores else 0
                        if max_score > 75:
                            # Find topic with highest score
                            best_topic_name = max(topic_scores, key=topic_scores.get)
                            best_topic = next((t for t in topics if t.name == best_topic_name), topics[0])
                            
                            article = Article(
                                title=entry_title,
                                url=entry_link,
                                content=content,
                                summary=analysis.get("summary", ""),
                                author=entry_author,
                                relevancy_score=max_score,
                                topic_scores=topic_scores,
                                feed_id=feed.id,
                                topic_id=best_topic.id,
                                published_date=published_date
                            )
                            
                            db.add(article)
                            db.commit()  # Commit each article immediately
                            processed_count += 1
                            print(f"  -> ✓ Article saved! Best topic: {best_topic.name} ({max_score}%) ({processed_count} total)")
                        else:
                            print(f"  -> All scores too low (max: {max_score}), skipping")
                    
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
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
from datetime import datetime
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
    
    def analyze_article(self, content, topics_text):
        prompt = f"""Analyze this article content against these topics: {topics_text}

    Article: {content[:2000]}

    Return ONLY a valid JSON object with no additional text: {{"relevancy_score": int (0-100), "is_relevant": bool, "summary": string}}"""
        
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
                return {
                    "relevancy_score": int(result.get("relevancy_score", 0)),
                    "is_relevant": result.get("is_relevant", False),
                    "summary": result.get("summary", "")
                }
            else:
                logger.error(f"AI returned non-dict response: {type(result)}")
                return {"relevancy_score": 0, "is_relevant": False, "summary": "Invalid response format"}
        except json.JSONDecodeError as e:
            logger.error(f"AI analysis JSON decode error: {e}")
            return {"relevancy_score": 0, "is_relevant": False, "summary": "JSON parsing failed"}
        except Exception as e:
            # Include the exception type and message for better diagnostics
            # For botocore ClientError, include the error response body
            try:
                error_response = getattr(e, 'response', {})
                logger.error(f"AI analysis error: {type(e).__name__}: {e}; response: {error_response}")
            except Exception:
                logger.error(f"AI analysis error: {type(e).__name__}: {e}")
            return {"relevancy_score": 0, "is_relevant": False, "summary": "Analysis failed"}

class NewsProcessor:
    def __init__(self, api_key=None):
        self.rss_fetcher = RSSFetcher()
        self.ai_service = AIService(api_key)
        self.processing = False
    
    def process_feeds(self):
        if self.processing:
            return "Already processing"
        
        self.processing = True
        try:
            db = get_db()
            feeds = db.query(Feed).filter(Feed.active == True).all()
            topics = db.query(Topic).filter(Topic.active == True).all()
            
            if not topics:
                return "No active topics found"
            
            topics_text = ", ".join([f"{t.name}: {t.keywords}" for t in topics])
            processed_count = 0
            
            for feed in feeds:
                entries = self.rss_fetcher.fetch_feed(feed.url)
                
                for entry in entries:
                    try:
                        # Safely get entry attributes
                        entry_link = getattr(entry, 'link', '')
                        entry_title = getattr(entry, 'title', 'Untitled')
                        
                        if not entry_link:
                            continue
                        
                        # Check if article already exists
                        existing = db.query(Article).filter(Article.url == entry_link).first()
                        if existing:
                            continue
                        
                        content = self.rss_fetcher.get_article_content(entry)
                        if not content:
                            continue
                        
                        # AI analysis with rate limiting
                        time.sleep(2)  # Rate limit protection
                        analysis = self.ai_service.analyze_article(content, topics_text)
                        
                        # Ensure analysis is a dict with valid score
                        if not isinstance(analysis, dict):
                            logger.warning(f"Invalid analysis response for {entry_title}")
                            continue
                        
                        relevancy_score = analysis.get("relevancy_score", 0)
                        if not isinstance(relevancy_score, int):
                            try:
                                relevancy_score = int(relevancy_score)
                            except (ValueError, TypeError):
                                relevancy_score = 0
                        
                        if relevancy_score > 75:
                            # Find best matching topic
                            best_topic = topics[0]  # Default to first topic
                            
                            article = Article(
                                title=entry_title,
                                url=entry_link,
                                content=content,
                                summary=analysis.get("summary", ""),
                                relevancy_score=relevancy_score,
                                feed_id=feed.id,
                                topic_id=best_topic.id,
                                published_date=datetime.now()
                            )
                            
                            db.add(article)
                            processed_count += 1
                    
                    except Exception as entry_error:
                        logger.error(f"Error processing entry: {entry_error}")
                        continue
            
            db.commit()
            db.close()
            return f"Processed {processed_count} relevant articles"
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return f"Error: {e}"
        finally:
            self.processing = False
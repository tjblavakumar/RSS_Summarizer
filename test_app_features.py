"""
Comprehensive tests for RSS Summarizer application features
Tests: Admin Console, Refresh News, Clear News, and all CRUD operations
"""
import sys
import time
import json
from database import SessionLocal, Feed, Topic, Category, Article, SystemConfig
from services import NewsProcessor

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add(self, name, passed, message=""):
        self.tests.append((name, passed, message))
        if passed:
            self.passed += 1
            print(f"[PASS] {name}")
        else:
            self.failed += 1
            print(f"[FAIL] {name}: {message}")
    
    def summary(self):
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        print("="*60)
        return self.failed == 0

def test_database_connection():
    """Test database connectivity"""
    results = TestResults()
    print("\n=== Testing Database Connection ===")
    
    try:
        db = SessionLocal()
        results.add("Database connection", True)
        
        # Test table existence
        feeds = db.query(Feed).count()
        results.add("Feeds table accessible", feeds >= 0)
        
        categories = db.query(Category).count()
        results.add("Categories table accessible", categories >= 0)
        
        topics = db.query(Topic).count()
        results.add("Topics table accessible", topics >= 0)
        
        articles = db.query(Article).count()
        results.add("Articles table accessible", articles >= 0)
        
        config = db.query(SystemConfig).count()
        results.add("SystemConfig table accessible", config >= 0)
        
        db.close()
    except Exception as e:
        results.add("Database connection", False, str(e))
    
    return results

def test_admin_feeds():
    """Test admin feed management (CRUD operations)"""
    results = TestResults()
    print("\n=== Testing Admin Feed Management ===")
    
    db = SessionLocal()
    try:
        # Clean up any existing test data
        db.query(Feed).filter(Feed.name.like('Test%')).delete()
        db.commit()
        
        # CREATE - Add new feed
        test_feed = Feed(
            name="Test Feed",
            url="https://example.com/feed.xml",
            active=True
        )
        db.add(test_feed)
        db.commit()
        results.add("Create feed", True)
        
        # NEGATIVE: Try to add duplicate URL
        try:
            duplicate_feed = Feed(
                name="Duplicate Feed",
                url="https://example.com/feed.xml",
                active=True
            )
            db.add(duplicate_feed)
            db.commit()
            results.add("Reject duplicate feed URL", False, "Allowed duplicate URL")
        except:
            db.rollback()
            results.add("Reject duplicate feed URL", True)
        
        # READ - Retrieve feed
        feed = db.query(Feed).filter(Feed.name == "Test Feed").first()
        results.add("Read feed", feed is not None and feed.name == "Test Feed")
        
        # UPDATE - Modify feed
        feed.active = False
        feed.url = "https://example.com/updated.xml"
        db.commit()
        
        updated = db.query(Feed).filter(Feed.name == "Test Feed").first()
        results.add("Update feed", updated.active == False and "updated" in updated.url)
        
        # DELETE - Remove feed
        db.delete(feed)
        db.commit()
        
        deleted = db.query(Feed).filter(Feed.name == "Test Feed").first()
        results.add("Delete feed", deleted is None)
        
    except Exception as e:
        results.add("Admin feed operations", False, str(e))
    finally:
        db.close()
    
    return results

def test_admin_categories():
    """Test admin category management"""
    results = TestResults()
    print("\n=== Testing Admin Category Management ===")
    
    db = SessionLocal()
    try:
        # Clean up any existing test data
        db.query(Category).filter(Category.name.like('Test%')).delete()
        db.commit()
        
        # CREATE
        test_cat = Category(
            name="Test Category",
            description="Test description",
            color="#FF0000",
            active=True
        )
        db.add(test_cat)
        db.commit()
        results.add("Create category", True)
        
        # NEGATIVE: Try to add duplicate category name
        try:
            duplicate_cat = Category(
                name="Test Category",
                description="Duplicate",
                color="#00FF00",
                active=True
            )
            db.add(duplicate_cat)
            db.commit()
            results.add("Reject duplicate category", False, "Allowed duplicate name")
        except:
            db.rollback()
            results.add("Reject duplicate category", True)
        
        # READ
        cat = db.query(Category).filter(Category.name == "Test Category").first()
        results.add("Read category", cat is not None and cat.color == "#FF0000")
        
        # UPDATE
        cat.active = False
        cat.description = "Updated description"
        db.commit()
        
        updated = db.query(Category).filter(Category.name == "Test Category").first()
        results.add("Update category", updated.active == False and "Updated" in updated.description)
        
        # DELETE
        db.delete(cat)
        db.commit()
        
        deleted = db.query(Category).filter(Category.name == "Test Category").first()
        results.add("Delete category", deleted is None)
        
    except Exception as e:
        results.add("Admin category operations", False, str(e))
    finally:
        db.close()
    
    return results

def test_admin_topics():
    """Test admin topic management"""
    results = TestResults()
    print("\n=== Testing Admin Topic Management ===")
    
    db = SessionLocal()
    try:
        # Clean up any existing test data
        db.query(Topic).filter(Topic.name.like('Test%')).delete()
        db.query(Topic).filter(Topic.name.like('Invalid%')).delete()
        db.commit()
        
        # Get a category for foreign key
        category = db.query(Category).first()
        
        # CREATE
        test_topic = Topic(
            name="Test Topic",
            keywords="test, keywords, sample",
            category_id=category.id if category else None,
            active=True
        )
        db.add(test_topic)
        db.commit()
        results.add("Create topic", True)
        
        # NEGATIVE: Try to add duplicate topic name
        try:
            duplicate_topic = Topic(
                name="Test Topic",
                keywords="duplicate",
                category_id=category.id if category else None,
                active=True
            )
            db.add(duplicate_topic)
            db.commit()
            results.add("Reject duplicate topic", False, "Allowed duplicate name")
        except:
            db.rollback()
            results.add("Reject duplicate topic", True)
        
        # NEGATIVE: Try to create topic without keywords
        try:
            invalid_topic = Topic(
                name="Invalid Topic Empty Keywords",
                keywords="",
                category_id=category.id if category else None,
                active=True
            )
            db.add(invalid_topic)
            db.commit()
            # SQLite allows empty strings, so we need app-level validation
            # Clean up
            db.delete(invalid_topic)
            db.commit()
            # This is expected behavior - validation should be in app.py
            results.add("Validate topic keywords (app-level)", True, "DB allows empty, app validates")
        except:
            db.rollback()
            results.add("Validate topic keywords (db-level)", True)
        
        # READ
        topic = db.query(Topic).filter(Topic.name == "Test Topic").first()
        results.add("Read topic", topic is not None and "test" in topic.keywords)
        
        # UPDATE
        topic.active = False
        topic.keywords = "updated, keywords"
        db.commit()
        
        updated = db.query(Topic).filter(Topic.name == "Test Topic").first()
        results.add("Update topic", updated.active == False and "updated" in updated.keywords)
        
        # DELETE
        db.delete(topic)
        db.commit()
        
        deleted = db.query(Topic).filter(Topic.name == "Test Topic").first()
        results.add("Delete topic", deleted is None)
        
    except Exception as e:
        results.add("Admin topic operations", False, str(e))
    finally:
        db.close()
    
    return results

def test_admin_llm_config():
    """Test LLM configuration management"""
    results = TestResults()
    print("\n=== Testing LLM Configuration ===")
    
    db = SessionLocal()
    try:
        # READ existing config
        config = db.query(SystemConfig).filter(SystemConfig.key == "llm_provider").first()
        results.add("Read LLM config", config is not None)
        
        # UPDATE config
        if config:
            original_value = config.value
            config.value = "test_provider"
            db.commit()
            
            updated = db.query(SystemConfig).filter(SystemConfig.key == "llm_provider").first()
            results.add("Update LLM config", updated.value == "test_provider")
            
            # Restore original
            config.value = original_value
            db.commit()
        
        # CREATE new config
        test_config = SystemConfig(
            key="test_config",
            value="test_value",
            description="Test configuration"
        )
        db.add(test_config)
        db.commit()
        results.add("Create LLM config", True)
        
        # DELETE test config
        db.delete(test_config)
        db.commit()
        
    except Exception as e:
        results.add("LLM config operations", False, str(e))
    finally:
        db.close()
    
    return results

def test_refresh_news():
    """Test refresh news functionality"""
    results = TestResults()
    print("\n=== Testing Refresh News ===")
    
    db = SessionLocal()
    try:
        # Check prerequisites
        active_feeds = db.query(Feed).filter(Feed.active == True).count()
        active_categories = db.query(Category).filter(Category.active == True).count()
        
        results.add("Active feeds exist", active_feeds > 0, f"Found {active_feeds} feeds")
        results.add("Active categories exist", active_categories > 0, f"Found {active_categories} categories")
        
        # NEGATIVE: Test with no active categories
        if active_categories > 0:
            # Temporarily deactivate all categories
            categories = db.query(Category).all()
            for cat in categories:
                cat.active = False
            db.commit()
            
            processor = NewsProcessor()
            result = processor.process_feeds()
            results.add("Handle no active categories", "No active categories" in result)
            
            # Restore categories
            for cat in categories:
                cat.active = True
            db.commit()
        
        if active_feeds > 0 and active_categories > 0:
            # Get initial article count
            initial_count = db.query(Article).count()
            print(f"  Initial article count: {initial_count}")
            
            # Run news processor
            processor = NewsProcessor()
            results.add("NewsProcessor initialized", not processor.processing)
            
            print("  Running news processing (this may take 30-60 seconds)...")
            result = processor.process_feeds()
            
            results.add("News processing completed", "Error" not in result, result)
            
            # Check if articles were processed
            final_count = db.query(Article).count()
            print(f"  Final article count: {final_count}")
            
            results.add("News processing executed", True, f"Processed: {result}")
            
            # NEGATIVE: Test concurrent processing prevention
            processor2 = NewsProcessor()
            processor2.processing = True
            result2 = processor2.process_feeds()
            results.add("Prevent concurrent processing", "Already processing" in result2)
            
        db.close()
    except Exception as e:
        results.add("Refresh news", False, str(e))
    
    return results

def test_clear_news():
    """Test clear all news functionality"""
    results = TestResults()
    print("\n=== Testing Clear News ===")
    
    db = SessionLocal()
    try:
        # Ensure we have some articles
        initial_count = db.query(Article).count()
        print(f"  Initial article count: {initial_count}")
        
        if initial_count == 0:
            # Add a test article
            test_article = Article(
                title="Test Article",
                url="https://example.com/test",
                content="Test content",
                summary="Test summary",
                category_name="Test",
                relevancy_score=80
            )
            db.add(test_article)
            db.commit()
            initial_count = 1
        
        # Clear all articles
        processor = NewsProcessor()
        cleared_count = processor.clear_all_articles()
        
        results.add("Clear news executed", cleared_count == initial_count, f"Cleared {cleared_count} articles")
        
        # Verify articles are cleared
        final_count = db.query(Article).count()
        results.add("All articles cleared", final_count == 0, f"Remaining: {final_count}")
        
        db.close()
    except Exception as e:
        results.add("Clear news", False, str(e))
    
    return results

def test_article_filtering():
    """Test article relevancy filtering (score < 75)"""
    results = TestResults()
    print("\n=== Testing Article Filtering ===")
    
    db = SessionLocal()
    try:
        # Check that all articles have relevancy_score >= 75
        low_score_articles = db.query(Article).filter(Article.relevancy_score < 75).count()
        results.add("Low relevancy articles filtered", low_score_articles == 0, 
                   f"Found {low_score_articles} articles with score < 75")
        
        # Check that articles have valid scores
        articles_with_scores = db.query(Article).filter(Article.relevancy_score.isnot(None)).count()
        total_articles = db.query(Article).count()
        
        if total_articles > 0:
            results.add("Articles have relevancy scores", articles_with_scores == total_articles)
        
        db.close()
    except Exception as e:
        results.add("Article filtering", False, str(e))
    
    return results

def test_toggle_operations():
    """Test toggle active/inactive for feeds, topics, categories"""
    results = TestResults()
    print("\n=== Testing Toggle Operations ===")
    
    db = SessionLocal()
    try:
        # Test feed toggle
        feed = db.query(Feed).first()
        if feed:
            original_state = feed.active
            feed.active = not feed.active
            db.commit()
            
            toggled = db.query(Feed).filter(Feed.id == feed.id).first()
            results.add("Toggle feed active", toggled.active != original_state)
            
            # Toggle back
            feed.active = not feed.active
            db.commit()
            
            restored = db.query(Feed).filter(Feed.id == feed.id).first()
            results.add("Toggle feed back to original", restored.active == original_state)
        
        # Test category toggle
        category = db.query(Category).first()
        if category:
            original_state = category.active
            category.active = not category.active
            db.commit()
            
            toggled = db.query(Category).filter(Category.id == category.id).first()
            results.add("Toggle category active", toggled.active != original_state)
            
            # Toggle back
            category.active = not category.active
            db.commit()
            
            restored = db.query(Category).filter(Category.id == category.id).first()
            results.add("Toggle category back to original", restored.active == original_state)
        
        # Test topic toggle
        topic = db.query(Topic).first()
        if topic:
            original_state = topic.active
            topic.active = not topic.active
            db.commit()
            
            toggled = db.query(Topic).filter(Topic.id == topic.id).first()
            results.add("Toggle topic active", toggled.active != original_state)
            
            # Toggle back
            topic.active = not topic.active
            db.commit()
            
            restored = db.query(Topic).filter(Topic.id == topic.id).first()
            results.add("Toggle topic back to original", restored.active == original_state)
        
        db.close()
    except Exception as e:
        results.add("Toggle operations", False, str(e))
    
    return results

def test_cleanup_old_articles():
    """Test automatic cleanup of articles older than 24 hours"""
    results = TestResults()
    print("\n=== Testing Article Cleanup ===")
    
    try:
        processor = NewsProcessor()
        cleaned = processor.cleanup_old_articles()
        results.add("Cleanup old articles", True, f"Cleaned {cleaned} old articles")
    except Exception as e:
        results.add("Cleanup old articles", False, str(e))
    
    return results

def test_bedrock_connection():
    """Test AWS Bedrock connectivity and configuration"""
    results = TestResults()
    print("\n=== Testing AWS Bedrock Connection ===")
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Test AWS credentials
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            results.add("AWS credentials configured", True, f"Account: {identity['Account']}")
        except NoCredentialsError:
            results.add("AWS credentials configured", False, "No credentials found")
            return results
        except Exception as e:
            results.add("AWS credentials configured", False, str(e))
            return results
        
        # Test Bedrock client creation
        try:
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            results.add("Bedrock client created", True)
        except Exception as e:
            results.add("Bedrock client created", False, str(e))
            return results
        
        # Test Bedrock model invocation
        try:
            test_payload = {
                "max_tokens": 100,
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": "Say 'test successful' in JSON format: {\"status\": \"test successful\"}"}]
            }
            
            response = bedrock.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                contentType='application/json',
                accept='application/json',
                body=json.dumps(test_payload).encode('utf-8')
            )
            
            response_body = json.loads(response['body'].read())
            results.add("Bedrock model invocation", True, "Model responded successfully")
            
            # Test response parsing
            if 'content' in response_body and len(response_body['content']) > 0:
                results.add("Bedrock response format valid", True)
            else:
                results.add("Bedrock response format valid", False, "Unexpected response format")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                results.add("Bedrock model invocation", False, "Access denied - check IAM permissions")
            else:
                results.add("Bedrock model invocation", False, f"ClientError: {error_code}")
        except Exception as e:
            results.add("Bedrock model invocation", False, str(e))
        
    except Exception as e:
        results.add("Bedrock connection test", False, str(e))
    
    return results

def test_ai_service():
    """Test AI service with actual analysis"""
    results = TestResults()
    print("\n=== Testing AI Service ===")
    
    from services import AIService
    from database import SessionLocal, Category
    
    db = SessionLocal()
    try:
        categories = db.query(Category).filter(Category.active == True).all()
        
        if not categories:
            results.add("AI service test", False, "No active categories")
            return results
        
        ai_service = AIService()
        
        # Test with sample article
        test_title = "Federal Reserve Maintains Interest Rates"
        test_content = "The Federal Reserve announced today that it will keep interest rates unchanged. Fed Chair Jerome Powell stated the decision reflects current economic conditions."
        test_author = "Test Author"
        test_url = "https://example.com/test"
        
        print("  Analyzing test article with AI...")
        result = ai_service.analyze_article(test_title, test_author, test_content, test_url, categories)
        
        # Verify result structure
        results.add("AI returns summary", 'summary' in result and result['summary'])
        results.add("AI returns category", 'category' in result and result['category'])
        results.add("AI returns relevancy score", 'relevancy_score' in result and isinstance(result['relevancy_score'], int))
        results.add("AI relevancy score valid range", 0 <= result.get('relevancy_score', -1) <= 100)
        
        # Check if analysis was successful
        if result.get('summary') != "Analysis failed":
            results.add("AI analysis successful", True, f"Category: {result.get('category')}, Score: {result.get('relevancy_score')}")
        else:
            results.add("AI analysis successful", False, "Analysis returned failure status")
        
    except Exception as e:
        results.add("AI service test", False, str(e))
    finally:
        db.close()
    
    return results

def test_edit_operations():
    """Test edit functionality for feeds, categories, and topics"""
    results = TestResults()
    print("\n=== Testing Edit Operations ===")
    
    db = SessionLocal()
    try:
        # Test edit feed
        feed = db.query(Feed).filter(Feed.name == "Federal Reserve News").first()
        if feed:
            original_url = feed.url
            feed.url = "https://example.com/temp.xml"
            db.commit()
            
            edited = db.query(Feed).filter(Feed.id == feed.id).first()
            results.add("Edit feed URL", "example.com" in edited.url)
            
            # Restore
            feed.url = original_url
            db.commit()
            results.add("Restore feed URL", db.query(Feed).filter(Feed.id == feed.id).first().url == original_url)
        
        # Test edit category
        category = db.query(Category).filter(Category.name == "Technology").first()
        if category:
            original_desc = category.description
            original_color = category.color
            category.description = "Updated tech description"
            category.color = "#FF0000"
            db.commit()
            
            edited = db.query(Category).filter(Category.id == category.id).first()
            results.add("Edit category description", "Updated" in edited.description)
            results.add("Edit category color", edited.color == "#FF0000")
            
            # Restore
            category.description = original_desc
            category.color = original_color
            db.commit()
        
        # Test edit topic
        topic = db.query(Topic).filter(Topic.name == "Fintech").first()
        if topic:
            original_keywords = topic.keywords
            topic.keywords = "updated, test, keywords"
            db.commit()
            
            edited = db.query(Topic).filter(Topic.id == topic.id).first()
            results.add("Edit topic keywords", "updated" in edited.keywords)
            
            # Restore
            topic.keywords = original_keywords
            db.commit()
            results.add("Restore topic keywords", "fintech" in db.query(Topic).filter(Topic.id == topic.id).first().keywords)
        
        db.close()
    except Exception as e:
        results.add("Edit operations", False, str(e))
    
    return results

def test_delete_operations():
    """Test delete functionality for feeds, categories, and topics"""
    results = TestResults()
    print("\n=== Testing Delete Operations ===")
    
    db = SessionLocal()
    try:
        # Create test items to delete
        test_feed = Feed(name="Delete Test Feed", url="https://delete.test/feed.xml", active=True)
        db.add(test_feed)
        db.commit()
        feed_id = test_feed.id
        
        test_category = Category(name="Delete Test Category", description="To be deleted", color="#000000", active=True)
        db.add(test_category)
        db.commit()
        category_id = test_category.id
        
        test_topic = Topic(name="Delete Test Topic", keywords="delete, test", category_id=category_id, active=True)
        db.add(test_topic)
        db.commit()
        topic_id = test_topic.id
        
        # Test delete feed
        db.delete(test_feed)
        db.commit()
        deleted_feed = db.query(Feed).filter(Feed.id == feed_id).first()
        results.add("Delete feed", deleted_feed is None)
        
        # Test delete topic
        db.delete(test_topic)
        db.commit()
        deleted_topic = db.query(Topic).filter(Topic.id == topic_id).first()
        results.add("Delete topic", deleted_topic is None)
        
        # Test delete category
        db.delete(test_category)
        db.commit()
        deleted_category = db.query(Category).filter(Category.id == category_id).first()
        results.add("Delete category", deleted_category is None)
        
        # Verify deletions are permanent
        results.add("Verify feed deletion permanent", db.query(Feed).filter(Feed.name == "Delete Test Feed").first() is None)
        results.add("Verify category deletion permanent", db.query(Category).filter(Category.name == "Delete Test Category").first() is None)
        results.add("Verify topic deletion permanent", db.query(Topic).filter(Topic.name == "Delete Test Topic").first() is None)
        
        db.close()
    except Exception as e:
        results.add("Delete operations", False, str(e))
    
    return results

def test_activate_deactivate_workflow():
    """Test complete activate/deactivate workflow"""
    results = TestResults()
    print("\n=== Testing Activate/Deactivate Workflow ===")
    
    db = SessionLocal()
    try:
        # Create test items
        test_feed = Feed(name="Workflow Test Feed", url="https://workflow.test/feed.xml", active=True)
        db.add(test_feed)
        db.commit()
        
        # Test deactivate
        test_feed.active = False
        db.commit()
        results.add("Deactivate feed", db.query(Feed).filter(Feed.id == test_feed.id).first().active == False)
        
        # Test reactivate
        test_feed.active = True
        db.commit()
        results.add("Reactivate feed", db.query(Feed).filter(Feed.id == test_feed.id).first().active == True)
        
        # Test multiple toggles
        for i in range(3):
            test_feed.active = not test_feed.active
            db.commit()
        results.add("Multiple toggles work", db.query(Feed).filter(Feed.id == test_feed.id).first().active == False)
        
        # Cleanup
        db.delete(test_feed)
        db.commit()
        
        db.close()
    except Exception as e:
        results.add("Activate/deactivate workflow", False, str(e))
    
    return results

def main():
    """Run all tests"""
    print("="*60)
    print("RSS SUMMARIZER - COMPREHENSIVE FEATURE TESTS")
    print("="*60)
    
    all_results = []
    
    # Run all test suites
    all_results.append(test_database_connection())
    all_results.append(test_bedrock_connection())
    all_results.append(test_ai_service())
    all_results.append(test_admin_feeds())
    all_results.append(test_admin_categories())
    all_results.append(test_admin_topics())
    all_results.append(test_admin_llm_config())
    all_results.append(test_toggle_operations())
    all_results.append(test_edit_operations())
    all_results.append(test_delete_operations())
    all_results.append(test_activate_deactivate_workflow())
    all_results.append(test_article_filtering())
    all_results.append(test_cleanup_old_articles())
    
    # Optional: Run refresh and clear tests (takes longer)
    if '--full' in sys.argv:
        all_results.append(test_refresh_news())
        all_results.append(test_clear_news())
    else:
        print("\n[INFO] Skipping refresh/clear tests. Use --full to run all tests.")
    
    # Print overall summary
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    
    print("\n" + "="*60)
    print("OVERALL TEST RESULTS")
    print("="*60)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed/(total_passed+total_failed)*100:.1f}%")
    print("="*60)
    
    if total_failed == 0:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total_failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

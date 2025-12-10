import sys
import os
from database import SessionLocal, Feed
from services import RSSFetcher

def verify_access_key_logic():
    print("Verifying access key logic...")
    
    # 1. Verify Database Schema
    db = SessionLocal()
    try:
        # Create a test feed with an access key
        test_feed_name = "Test Access Key Feed"
        test_feed_url = "https://httpbin.org/headers" # Returns headers as JSON
        test_access_key = "secret-token-123"
        
        # Check if exists and delete
        existing = db.query(Feed).filter(Feed.name == test_feed_name).first()
        if existing:
            db.delete(existing)
            db.commit()
            
        feed = Feed(name=test_feed_name, url=test_feed_url, access_key=test_access_key)
        db.add(feed)
        db.commit()
        print("✓ Database: Successfully added feed with access_key")
        
        # 2. Verify Fetcher Logic
        # We use httpbin.org/headers which returns the headers sent to it
        fetcher = RSSFetcher()
        # We need to mock the parsing because httpbin returns JSON, not RSS
        # But we want to see if the headers were sent.
        # So we'll inspect the fetcher's behavior or just call it and catch the parse error,
        # but we really want to know if the header was sent.
        
        # Let's monkeypatch requests.get to intercept the call
        import requests
        original_get = requests.get
        
        captured_headers = {}
        
        def mock_get(url, headers=None, **kwargs):
            nonlocal captured_headers
            captured_headers = headers
            return original_get(url, headers=headers, **kwargs)
            
        requests.get = mock_get
        
        try:
            print("Testing fetch with access key...")
            fetcher.fetch_feed(test_feed_url, access_key=test_access_key)
        except Exception as e:
            # Expected to fail parsing JSON as RSS
            pass
        finally:
            requests.get = original_get
            
        if captured_headers.get('Authorization') == test_access_key:
            print(f"✓ Fetcher: Authorization header sent correctly: {captured_headers.get('Authorization')}")
        else:
            print(f"✗ Fetcher: Authorization header MISSING or incorrect. Got: {captured_headers}")

        if captured_headers.get('API-Key') == test_access_key:
             print(f"✓ Fetcher: API-Key header sent correctly")

        # Cleanup
        db.delete(feed)
        db.commit()
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_access_key_logic()

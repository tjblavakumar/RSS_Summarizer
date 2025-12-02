#!/usr/bin/env python3
"""Test AI summarization with sample data"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services import AIService
from database import get_db, Category

def test_ai_summary():
    """Test AI summarization with sample article"""
    
    # Sample article data
    title = "Federal Reserve Announces New Interest Rate Policy"
    author = "John Smith"
    url = "https://example.com/fed-policy"
    content = """The Federal Reserve announced today a new monetary policy framework that will guide interest rate decisions for the coming year. Fed Chair Jerome Powell stated that the central bank will maintain its current approach to inflation targeting while monitoring employment levels closely. The decision comes amid ongoing economic uncertainty and follows extensive deliberation by the Federal Open Market Committee. Powell emphasized the importance of data-driven decisions in monetary policy. The announcement has significant implications for banking institutions and financial markets across the 12th District."""
    
    # Get categories from database
    db = get_db()
    try:
        categories = db.query(Category).filter(Category.active == True).all()
        if not categories:
            print("No active categories found in database")
            return
        
        print(f"Available categories: {[c.name for c in categories]}")
        
        # Test AI analysis
        ai_service = AIService()
        print("\nTesting AI analysis...")
        
        result = ai_service.analyze_article(title, author, content, url, categories)
        
        print("\n=== AI ANALYSIS RESULT ===")
        print(f"Summary: {result.get('summary', 'N/A')}")
        print(f"Quotes: {result.get('quotes', 'N/A')}")
        print(f"Category: {result.get('category', 'N/A')}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_summary()
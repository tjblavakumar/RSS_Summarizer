#!/usr/bin/env python3
"""SQLite database validation script"""

import sqlite3
import sys
import os

def check_database():
    """Connect to SQLite and validate data"""
    db_path = 'news.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", [t[0] for t in tables])
        
        # Check feeds
        cursor.execute("SELECT COUNT(*) FROM feeds")
        feed_count = cursor.fetchone()[0]
        print(f"Feeds: {feed_count}")
        
        # Check categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        print(f"Categories: {category_count}")
        
        # Check topics
        cursor.execute("SELECT COUNT(*) FROM topics")
        topic_count = cursor.fetchone()[0]
        print(f"Topics: {topic_count}")
        
        # Check articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        print(f"Articles: {article_count}")
        
        # Show recent articles
        cursor.execute("SELECT title, created_at FROM articles ORDER BY created_at DESC LIMIT 5")
        recent = cursor.fetchall()
        print("\nRecent articles:")
        for title, created_at in recent:
            print(f"  {created_at}: {title[:50]}...")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()
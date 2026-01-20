#!/usr/bin/env python3
"""
Initialize SQLite database for RSS Summarizer
Works on Amazon Linux 2 and other Linux distributions
Usage: python3 init_db_sql.py [--force]
"""

import sqlite3
import sys
from datetime import datetime

def init_database(force=False):
    db_file = 'news.db'
    
    # Backup existing database
    if force:
        import shutil
        try:
            backup_file = f'news.db.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            shutil.copy(db_file, backup_file)
            print(f"Backed up existing database to {backup_file}")
        except FileNotFoundError:
            pass
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        print("Clearing existing data...")
        cursor.execute("DELETE FROM topics")
        cursor.execute("DELETE FROM feeds")
        cursor.execute("DELETE FROM categories")
        cursor.execute("DELETE FROM system_config")
        cursor.execute("DELETE FROM articles")
        
        # Insert Categories
        print("Adding categories...")
        categories = [
            (1, 'Financial System', 'Banking, Federal Reserve, monetary policy', '#1e3a8a', 1),
            (2, 'Economic Indicators', 'GDP, employment, inflation, economic data', '#059669', 1),
            (3, 'Markets', 'Stock markets, bonds, commodities', '#dc2626', 1),
            (4, 'Technology', 'Tech companies, innovation, digital transformation', '#7c3aed', 1),
            (5, 'Global Economy', 'International trade, global markets', '#ea580c', 1)
        ]
        cursor.executemany(
            "INSERT INTO categories (id, name, description, color, active) VALUES (?, ?, ?, ?, ?)",
            categories
        )
        
        # Insert RSS Feeds
        print("Adding RSS feeds...")
        feeds = [
            (1, 'Federal Reserve News', 'https://www.federalreserve.gov/feeds/press_all.xml', 1, None),
            (2, 'Reuters Business', 'https://feeds.reuters.com/reuters/businessNews', 1, None),
            (3, 'Reuters Economy', 'https://feeds.reuters.com/reuters/economyNews', 1, None),
            (4, 'Bloomberg Markets', 'https://feeds.bloomberg.com/markets/news.rss', 1, None),
            (5, 'CNBC Top News', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', 1, None),
            (6, 'Financial Times', 'https://www.ft.com/?format=rss', 1, None),
            (7, 'Wall Street Journal', 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', 1, None)
        ]
        cursor.executemany(
            "INSERT INTO feeds (id, name, url, active, access_key) VALUES (?, ?, ?, ?, ?)",
            feeds
        )
        
        # Insert Topics
        print("Adding topics...")
        topics = [
            (1, 'Federal Reserve Policy', 'federal reserve, fed, monetary policy, interest rates, FOMC, Jerome Powell, central bank', 1, 1),
            (2, 'Banking Sector', 'banks, banking, financial institutions, JPMorgan, Bank of America, Wells Fargo, credit', 1, 1),
            (3, 'Inflation', 'inflation, CPI, consumer prices, price increases, deflation, PCE', 2, 1),
            (4, 'Employment', 'jobs, employment, unemployment, labor market, payrolls, wages, hiring', 2, 1),
            (5, 'GDP & Growth', 'GDP, economic growth, recession, expansion, productivity', 2, 1),
            (6, 'Stock Markets', 'stocks, S&P 500, Dow Jones, Nasdaq, equity, shares, market rally, market decline', 3, 1),
            (7, 'Bond Markets', 'bonds, treasury, yields, fixed income, debt securities', 3, 1),
            (8, 'Fintech', 'fintech, digital banking, cryptocurrency, blockchain, payment technology', 4, 1),
            (9, 'Global Trade', 'trade, tariffs, exports, imports, trade war, international commerce', 5, 1)
        ]
        cursor.executemany(
            "INSERT INTO topics (id, name, keywords, category_id, active) VALUES (?, ?, ?, ?, ?)",
            topics
        )
        
        # Insert System Configuration
        print("Adding system configuration...")
        configs = [
            ('llm_provider', 'bedrock', 'LLM provider (bedrock/openai)'),
            ('llm_model', 'anthropic.claude-3-haiku-20240307-v1:0', 'Model ID'),
            ('llm_api_key', '', 'API key if needed'),
            ('llm_api_base', '', 'API base URL if needed')
        ]
        cursor.executemany(
            "INSERT INTO system_config (key, value, description) VALUES (?, ?, ?)",
            configs
        )
        
        conn.commit()
        
        print("\n==========================================")
        print("Database initialized successfully!")
        print(f"  - {len(categories)} categories")
        print(f"  - {len(feeds)} RSS feeds")
        print(f"  - {len(topics)} topics")
        print(f"  - {len(configs)} system configs")
        print("==========================================")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    force = '--force' in sys.argv or '-f' in sys.argv
    init_database(force=force)

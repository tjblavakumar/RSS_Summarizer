"""
Migration script to add unique constraints to feeds, categories, and topics
"""
import sqlite3
import shutil
from datetime import datetime

# Backup database first
backup_file = f"news_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2("news.db", backup_file)
print(f"Database backed up to: {backup_file}")

conn = sqlite3.connect('news.db')
cursor = conn.cursor()

try:
    print("\nApplying database migrations...")
    
    # Create new tables with unique constraints
    print("1. Creating new feeds table with unique constraints...")
    cursor.execute("""
        CREATE TABLE feeds_new (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            url VARCHAR(500) NOT NULL UNIQUE,
            active BOOLEAN DEFAULT 1,
            access_key VARCHAR(500)
        )
    """)
    
    # Copy data, removing duplicates
    cursor.execute("""
        INSERT INTO feeds_new (id, name, url, active, access_key)
        SELECT id, name, url, active, access_key
        FROM feeds
        WHERE id IN (
            SELECT MIN(id) FROM feeds GROUP BY url
        )
    """)
    
    cursor.execute("DROP TABLE feeds")
    cursor.execute("ALTER TABLE feeds_new RENAME TO feeds")
    print("   Feeds table migrated successfully")
    
    # Create new categories table
    print("2. Creating new categories table with unique constraints...")
    cursor.execute("""
        CREATE TABLE categories_new (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            color VARCHAR(7) DEFAULT '#007bff',
            active BOOLEAN DEFAULT 1
        )
    """)
    
    cursor.execute("""
        INSERT INTO categories_new (id, name, description, color, active)
        SELECT id, name, description, color, active
        FROM categories
        WHERE id IN (
            SELECT MIN(id) FROM categories GROUP BY name
        )
    """)
    
    cursor.execute("DROP TABLE categories")
    cursor.execute("ALTER TABLE categories_new RENAME TO categories")
    print("   Categories table migrated successfully")
    
    # Create new topics table
    print("3. Creating new topics table with unique constraints...")
    cursor.execute("""
        CREATE TABLE topics_new (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            keywords TEXT NOT NULL,
            category_id INTEGER,
            active BOOLEAN DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    
    cursor.execute("""
        INSERT INTO topics_new (id, name, keywords, category_id, active)
        SELECT id, name, keywords, category_id, active
        FROM topics
        WHERE id IN (
            SELECT MIN(id) FROM topics GROUP BY name
        )
    """)
    
    cursor.execute("DROP TABLE topics")
    cursor.execute("ALTER TABLE topics_new RENAME TO topics")
    print("   Topics table migrated successfully")
    
    conn.commit()
    print("\n[SUCCESS] All migrations completed successfully!")
    print(f"Backup saved at: {backup_file}")
    
except Exception as e:
    conn.rollback()
    print(f"\n[ERROR] Migration failed: {e}")
    print(f"Database can be restored from: {backup_file}")
    raise
finally:
    conn.close()

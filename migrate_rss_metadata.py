import sqlite3

# Add rss_metadata column to articles table
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE articles ADD COLUMN rss_metadata TEXT")
    conn.commit()
    print("Successfully added rss_metadata column")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column rss_metadata already exists")
    else:
        print(f"Error: {e}")
finally:
    conn.close()
